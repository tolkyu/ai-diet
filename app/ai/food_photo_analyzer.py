import base64
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.client import openai_client
from app.ai.nutrition_analyzer import FoodAnalysisResult, FoodItem, NutritionAnalyzer
from app.ai.prompts.photo_analysis import PHOTO_SYSTEM_PROMPT, PHOTO_ANALYSIS_TEMPLATE
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
from app.models.ai_analysis import AIAnalysis
from app.core.constants import AnalysisType, LOW_CONFIDENCE_THRESHOLD

logger = get_logger(__name__)


class FoodPhotoAnalyzer:
    def __init__(self) -> None:
        self._text_analyzer = NutritionAnalyzer()

    async def analyze_photo(
        self,
        photo_bytes: bytes,
        user_id: uuid.UUID | None = None,
        photo_url: str | None = None,
        session: AsyncSession | None = None,
    ) -> FoodAnalysisResult:
        image_b64 = base64.b64encode(photo_bytes).decode("utf-8")
        try:
            content, prompt_tokens, completion_tokens = await openai_client.vision_completion(
                text_prompt=PHOTO_ANALYSIS_TEMPLATE,
                image_base64=image_b64,
                system_prompt=PHOTO_SYSTEM_PROMPT,
            )

            # Strip markdown code fences if model wraps JSON in ```json ... ```
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```", 2)[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.rsplit("```", 1)[0].strip()

            data = json.loads(cleaned)
            result = self._text_analyzer._parse_response(data)
            result.meal_type_guess = data.get("meal_type_guess")  # type: ignore[attr-defined]
            result.food_quality_note = data.get("food_quality_note")  # type: ignore[attr-defined]

            if session and user_id:
                analysis = AIAnalysis(
                    user_id=user_id,
                    analysis_type=AnalysisType.FOOD_PHOTO,
                    input_photo_url=photo_url,
                    output_json=data,
                    tokens_used=prompt_tokens + completion_tokens,
                    confidence_score=result.overall_confidence,
                )
                session.add(analysis)
                await session.flush()

            return result
        except json.JSONDecodeError as e:
            logger.error("Failed to parse photo analysis JSON", error=str(e), raw_content=content[:500])
            raise AIServiceError("Could not analyze food photo")

    async def analyze_photo_with_followup(
        self,
        photo_bytes: bytes,
        followup_answer: str,
        initial_result: FoodAnalysisResult,
        user_id: uuid.UUID | None = None,
        session: AsyncSession | None = None,
    ) -> FoodAnalysisResult:
        combined_text = (
            f"Previous analysis items: {', '.join(i.name for i in initial_result.items)}. "
            f"User clarification: {followup_answer}"
        )
        from app.ai.prompts.food_analysis import SYSTEM_PROMPT, FOOD_ANALYSIS_TEMPLATE
        prompt = FOOD_ANALYSIS_TEMPLATE.format(food_text=combined_text)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        content, _, _ = await openai_client.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        data = json.loads(content)
        return self._text_analyzer._parse_response(data)


food_photo_analyzer = FoodPhotoAnalyzer()
