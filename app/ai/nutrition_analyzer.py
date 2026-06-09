import json
import uuid
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.client import openai_client
from app.ai.prompts.food_analysis import SYSTEM_PROMPT, FOOD_ANALYSIS_TEMPLATE
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
from app.models.ai_analysis import AIAnalysis
from app.core.constants import AnalysisType

logger = get_logger(__name__)


@dataclass
class FoodItem:
    name: str
    amount_g: float | None
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    confidence_score: float
    notes: str | None = None


@dataclass
class FoodAnalysisResult:
    items: list[FoodItem]
    total_calories: float
    total_protein_g: float
    total_fat_g: float
    total_carbs_g: float
    overall_confidence: float
    clarification_needed: bool
    clarification_question: str | None


class NutritionAnalyzer:
    async def analyze_text(
        self,
        food_text: str,
        user_id: uuid.UUID | None = None,
        session: AsyncSession | None = None,
    ) -> FoodAnalysisResult:
        prompt = FOOD_ANALYSIS_TEMPLATE.format(food_text=food_text)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            content, prompt_tokens, completion_tokens = await openai_client.chat_completion(
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            data = json.loads(content)
            result = self._parse_response(data)

            # Persist analysis record
            if session and user_id:
                analysis = AIAnalysis(
                    user_id=user_id,
                    analysis_type=AnalysisType.FOOD_TEXT,
                    input_text=food_text,
                    output_json=data,
                    model_used=None,
                    tokens_used=prompt_tokens + completion_tokens,
                    confidence_score=result.overall_confidence,
                )
                session.add(analysis)
                await session.flush()

            return result
        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response JSON", error=str(e))
            raise AIServiceError("Could not parse food analysis response")

    def _parse_response(self, data: dict) -> FoodAnalysisResult:
        items = []
        for item_data in data.get("items", []):
            items.append(
                FoodItem(
                    name=item_data.get("name", "Unknown"),
                    amount_g=item_data.get("amount_g"),
                    calories=float(item_data.get("calories", 0)),
                    protein_g=float(item_data.get("protein_g", 0)),
                    fat_g=float(item_data.get("fat_g", 0)),
                    carbs_g=float(item_data.get("carbs_g", 0)),
                    confidence_score=float(item_data.get("confidence_score", 0.8)),
                    notes=item_data.get("notes"),
                )
            )

        return FoodAnalysisResult(
            items=items,
            total_calories=float(data.get("total_calories", 0)),
            total_protein_g=float(data.get("total_protein_g", 0)),
            total_fat_g=float(data.get("total_fat_g", 0)),
            total_carbs_g=float(data.get("total_carbs_g", 0)),
            overall_confidence=float(data.get("overall_confidence", 0.8)),
            clarification_needed=bool(data.get("clarification_needed", False)),
            clarification_question=data.get("clarification_question"),
        )

    def format_entries_for_db(self, result: FoodAnalysisResult) -> list[dict]:
        return [
            {
                "name": item.name,
                "amount_g": item.amount_g,
                "calories": item.calories,
                "protein_g": item.protein_g,
                "fat_g": item.fat_g,
                "carbs_g": item.carbs_g,
                "confidence_score": item.confidence_score,
            }
            for item in result.items
        ]


nutrition_analyzer = NutritionAnalyzer()
