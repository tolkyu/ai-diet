"""
Unit tests for BMR/TDEE/macro calculations.
All expected values computed manually using documented formulas.
"""
import pytest
from app.services.nutrition_service import NutritionService
from app.core.constants import GoalType, ActivityLevel, GoalIntensity


@pytest.fixture
def svc() -> NutritionService:
    return NutritionService()


class TestBMR:
    def test_male_bmr(self, svc):
        # BMR = (10 × 80) + (6.25 × 180) − (5 × 30) + 5 = 800 + 1125 − 150 + 5 = 1780
        bmr = svc.calculate_bmr("male", weight_kg=80, height_cm=180, age=30)
        assert bmr == pytest.approx(1780.0, abs=1.0)

    def test_female_bmr(self, svc):
        # BMR = (10 × 60) + (6.25 × 165) − (5 × 25) − 161 = 600 + 1031.25 − 125 − 161 = 1345.25
        bmr = svc.calculate_bmr("female", weight_kg=60, height_cm=165, age=25)
        assert bmr == pytest.approx(1345.25, abs=1.0)

    def test_bmr_increases_with_weight(self, svc):
        bmr_70 = svc.calculate_bmr("male", 70, 175, 30)
        bmr_90 = svc.calculate_bmr("male", 90, 175, 30)
        assert bmr_90 > bmr_70

    def test_bmr_decreases_with_age(self, svc):
        bmr_25 = svc.calculate_bmr("male", 80, 180, 25)
        bmr_50 = svc.calculate_bmr("male", 80, 180, 50)
        assert bmr_50 < bmr_25


class TestTDEE:
    def test_sedentary_multiplier(self, svc):
        bmr = 1780.0
        tdee = svc.calculate_tdee(bmr, "sedentary")
        assert tdee == pytest.approx(1780 * 1.2, abs=1.0)

    def test_athlete_multiplier(self, svc):
        bmr = 1780.0
        tdee = svc.calculate_tdee(bmr, "athlete")
        assert tdee == pytest.approx(1780 * 1.9, abs=1.0)

    def test_all_activity_levels_increase_tdee(self, svc):
        levels = ["sedentary", "lightly_active", "moderately_active", "very_active", "athlete"]
        tdees = [svc.calculate_tdee(2000, level) for level in levels]
        for i in range(len(tdees) - 1):
            assert tdees[i] < tdees[i + 1]


class TestCalorieTarget:
    def test_maintenance_equals_tdee(self, svc):
        target = svc.calculate_calorie_target(2200, "maintain", None)
        assert target == 2200.0

    def test_mild_deficit(self, svc):
        target = svc.calculate_calorie_target(2000, "lose_weight", "mild")
        assert target == pytest.approx(1750, abs=1.0)

    def test_moderate_deficit(self, svc):
        target = svc.calculate_calorie_target(2000, "lose_weight", "moderate")
        assert target == pytest.approx(1500, abs=1.0)

    def test_minimum_calories_enforced(self, svc):
        # Very low TDEE + aggressive deficit should not go below 1200
        target = svc.calculate_calorie_target(1700, "lose_weight", "aggressive")
        assert target >= 1200.0

    def test_slow_bulk(self, svc):
        target = svc.calculate_calorie_target(2000, "gain_muscle", "slow")
        assert target == pytest.approx(2200, abs=1.0)


class TestMacros:
    def test_protein_target_for_weight_loss(self, svc):
        protein_g, _, _ = svc.calculate_macros(1800, weight_kg=80, goal_type="lose_weight")
        expected = 2.2 * 80  # 176g
        assert protein_g == pytest.approx(expected, abs=1.0)

    def test_fat_is_27_5_pct(self, svc):
        calories = 2000
        _, fat_g, _ = svc.calculate_macros(calories, weight_kg=75, goal_type="maintain")
        expected_fat = (0.275 * calories) / 9
        assert fat_g == pytest.approx(expected_fat, abs=1.0)

    def test_carbs_fill_remaining(self, svc):
        calories = 2000
        protein_g, fat_g, carbs_g = svc.calculate_macros(calories, 75, "maintain")
        total_kcal = protein_g * 4 + fat_g * 9 + carbs_g * 4
        assert total_kcal == pytest.approx(calories, abs=10.0)

    def test_minimum_carbs_enforced(self, svc):
        # With very high protein target, carbs should not go below 50g
        _, _, carbs_g = svc.calculate_macros(1300, weight_kg=90, goal_type="lose_weight")
        assert carbs_g >= 50.0


class TestFullCalculation:
    def test_complete_calculation_male_weight_loss(self, svc):
        targets = svc.calculate_targets(
            gender="male",
            weight_kg=85,
            height_cm=178,
            age=32,
            activity_level="moderately_active",
            goal_type="lose_weight",
            intensity="moderate",
        )
        assert targets.bmr > 0
        assert targets.tdee > targets.bmr
        assert targets.calories < targets.tdee  # deficit
        assert targets.protein_g > 0
        assert targets.fat_g > 0
        assert targets.carbs_g > 0

    def test_muscle_gain_has_surplus(self, svc):
        targets = svc.calculate_targets(
            gender="male",
            weight_kg=70,
            height_cm=175,
            age=25,
            activity_level="very_active",
            goal_type="gain_muscle",
            intensity="moderate",
        )
        assert targets.calories > targets.tdee

    def test_weekly_loss_rate(self, svc):
        rate = svc.estimate_weekly_loss_gain_kg("lose_weight", "moderate")
        assert rate == pytest.approx(-0.45, abs=0.05)

    def test_weekly_gain_rate(self, svc):
        rate = svc.estimate_weekly_loss_gain_kg("gain_muscle", "slow")
        assert rate == pytest.approx(0.18, abs=0.05)
