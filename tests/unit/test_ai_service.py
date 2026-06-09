import json
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
class TestNutritionAnalyzer:
    async def test_analyze_text_returns_food_items(self):
        from app.ai.nutrition_analyzer import NutritionAnalyzer

        mock_response = json.dumps({
            "items": [
                {
                    "name": "Chicken breast",
                    "amount_g": 200,
                    "calories": 330,
                    "protein_g": 62,
                    "fat_g": 7,
                    "carbs_g": 0,
                    "confidence_score": 0.95,
                }
            ],
            "total_calories": 330,
            "total_protein_g": 62,
            "total_fat_g": 7,
            "total_carbs_g": 0,
            "overall_confidence": 0.95,
            "clarification_needed": False,
            "clarification_question": None,
        })

        analyzer = NutritionAnalyzer()
        with patch(
            "app.ai.nutrition_analyzer.openai_client.chat_completion",
            new_callable=AsyncMock,
            return_value=(mock_response, 50, 200),
        ):
            result = await analyzer.analyze_text("200g chicken breast")

        assert len(result.items) == 1
        assert result.items[0].name == "Chicken breast"
        assert result.total_calories == pytest.approx(330, abs=1)
        assert not result.clarification_needed

    async def test_analyze_text_returns_clarification_when_needed(self):
        from app.ai.nutrition_analyzer import NutritionAnalyzer

        mock_response = json.dumps({
            "items": [{"name": "Rice", "amount_g": 150, "calories": 195, "protein_g": 4, "fat_g": 0.5, "carbs_g": 42, "confidence_score": 0.5}],
            "total_calories": 195,
            "total_protein_g": 4,
            "total_fat_g": 0.5,
            "total_carbs_g": 42,
            "overall_confidence": 0.5,
            "clarification_needed": True,
            "clarification_question": "Was that approximately 100g or 200g of rice?",
        })

        analyzer = NutritionAnalyzer()
        with patch(
            "app.ai.nutrition_analyzer.openai_client.chat_completion",
            new_callable=AsyncMock,
            return_value=(mock_response, 40, 150),
        ):
            result = await analyzer.analyze_text("some rice")

        assert result.clarification_needed
        assert "100g or 200g" in result.clarification_question  # type: ignore[operator]

    async def test_format_entries_for_db(self):
        from app.ai.nutrition_analyzer import NutritionAnalyzer, FoodAnalysisResult, FoodItem

        analyzer = NutritionAnalyzer()
        result = FoodAnalysisResult(
            items=[FoodItem("Apple", 150, 78, 0.4, 0.2, 20.6, 0.9)],
            total_calories=78,
            total_protein_g=0.4,
            total_fat_g=0.2,
            total_carbs_g=20.6,
            overall_confidence=0.9,
            clarification_needed=False,
            clarification_question=None,
        )
        entries = analyzer.format_entries_for_db(result)
        assert len(entries) == 1
        assert entries[0]["name"] == "Apple"
        assert entries[0]["calories"] == 78


@pytest.mark.asyncio
class TestAICoach:
    async def test_morning_message_uses_template_data(self):
        from app.ai.coach import AICoach

        coach = AICoach()
        with patch(
            "app.ai.coach.openai_client.chat_completion",
            new_callable=AsyncMock,
            return_value=("Great morning! Hit 2000 kcal today.", 80, 50),
        ) as mock_chat:
            result = await coach.generate_morning_message({
                "user_id": None,
                "name": "John",
                "goal_type": "lose_weight",
                "intensity": "moderate",
                "calories": 1800,
                "protein_g": 160,
                "fat_g": 60,
                "carbs_g": 180,
                "weight_kg": 85,
                "days_tracking": 7,
                "yesterday_calories": 1750,
                "yesterday_protein": 155,
            })

        assert result == "Great morning! Hit 2000 kcal today."
        assert mock_chat.called
