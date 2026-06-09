"""
Nutrition calculation service implementing Mifflin-St Jeor BMR formula.

All formulas are documented below and in app/core/constants.py.

BMR (Mifflin-St Jeor, 1990):
  Male:   BMR = (10 × weight_kg) + (6.25 × height_cm) − (5 × age) + 5
  Female: BMR = (10 × weight_kg) + (6.25 × height_cm) − (5 × age) − 161

TDEE = BMR × activity_multiplier

Calorie target = TDEE + goal_adjustment (see GoalIntensity in constants.py)

Macros:
  Protein = protein_per_kg_target × weight_kg
  Fat     = fat_fraction × calorie_target / 9 kcal/g
  Carbs   = (calorie_target − protein_kcal − fat_kcal) / 4 kcal/g
"""
from dataclasses import dataclass
from decimal import Decimal

from app.core.constants import (
    ACTIVITY_MULTIPLIERS,
    CALORIE_ADJUSTMENTS,
    FAT_FRACTION,
    KCAL_PER_GRAM_CARB,
    KCAL_PER_GRAM_FAT,
    KCAL_PER_GRAM_PROTEIN,
    PROTEIN_PER_KG,
    ActivityLevel,
    Gender,
    GoalIntensity,
    GoalType,
)


@dataclass
class NutritionTargets:
    bmr: float
    tdee: float
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float


class NutritionService:

    def calculate_bmr(self, gender: str, weight_kg: float, height_cm: float, age: int) -> float:
        base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
        return base + 5 if gender == Gender.MALE else base - 161

    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        multiplier = ACTIVITY_MULTIPLIERS[ActivityLevel(activity_level)]
        return bmr * multiplier

    def calculate_calorie_target(
        self, tdee: float, goal_type: str, intensity: str | None
    ) -> float:
        if goal_type == GoalType.MAINTAIN or intensity is None:
            return tdee
        adjustment = CALORIE_ADJUSTMENTS[GoalIntensity(intensity)]
        # Enforce minimum safe calories: 1200 for women, 1500 for men
        return max(tdee + adjustment, 1200.0)

    def calculate_macros(
        self, calorie_target: float, weight_kg: float, goal_type: str
    ) -> tuple[float, float, float]:
        protein_per_kg = PROTEIN_PER_KG[GoalType(goal_type)]
        protein_g = protein_per_kg * weight_kg
        protein_kcal = protein_g * KCAL_PER_GRAM_PROTEIN

        fat_g = (FAT_FRACTION * calorie_target) / KCAL_PER_GRAM_FAT
        fat_kcal = fat_g * KCAL_PER_GRAM_FAT

        remaining_kcal = calorie_target - protein_kcal - fat_kcal
        carbs_g = max(remaining_kcal / KCAL_PER_GRAM_CARB, 50.0)  # minimum 50g carbs

        return round(protein_g, 1), round(fat_g, 1), round(carbs_g, 1)

    def calculate_targets(
        self,
        gender: str,
        weight_kg: float,
        height_cm: float,
        age: int,
        activity_level: str,
        goal_type: str,
        intensity: str | None = None,
    ) -> NutritionTargets:
        bmr = self.calculate_bmr(gender, weight_kg, height_cm, age)
        tdee = self.calculate_tdee(bmr, activity_level)
        calories = self.calculate_calorie_target(tdee, goal_type, intensity)
        protein_g, fat_g, carbs_g = self.calculate_macros(calories, weight_kg, goal_type)

        return NutritionTargets(
            bmr=round(bmr, 1),
            tdee=round(tdee, 1),
            calories=round(calories, 1),
            protein_g=protein_g,
            fat_g=fat_g,
            carbs_g=carbs_g,
        )

    def estimate_weekly_loss_gain_kg(self, goal_type: str, intensity: str | None) -> float:
        """Returns estimated kg change per week (negative = loss, positive = gain)."""
        if goal_type == GoalType.MAINTAIN or intensity is None:
            return 0.0
        adjustment_kcal = CALORIE_ADJUSTMENTS[GoalIntensity(intensity)]
        # 7700 kcal ≈ 1 kg body tissue
        return round((adjustment_kcal * 7) / 7700, 2)
