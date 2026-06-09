import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.client import openai_client
from app.ai.prompts.coaching import (
    COACH_SYSTEM_PROMPT,
    DAILY_MORNING_TEMPLATE,
    EVENING_CHECK_TEMPLATE,
    WEEKLY_SUMMARY_TEMPLATE,
    WEIGHT_ASSESSMENT_TEMPLATE,
)
from app.core.constants import AnalysisType, GoalType
from app.core.logging import get_logger
from app.models.ai_analysis import AIAnalysis

logger = get_logger(__name__)


class AICoach:
    async def generate_morning_message(
        self,
        user_data: dict,
        session: AsyncSession | None = None,
    ) -> str:
        prompt = DAILY_MORNING_TEMPLATE.format(**user_data)
        messages = [
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        content, tokens_in, tokens_out = await openai_client.chat_completion(
            messages=messages, temperature=0.7
        )

        if session and user_data.get("user_id"):
            await self._save_analysis(
                session,
                user_id=user_data["user_id"],
                analysis_type=AnalysisType.COACHING_DAILY,
                output=content,
                tokens=tokens_in + tokens_out,
            )

        return content

    async def generate_evening_check(
        self,
        user_data: dict,
        session: AsyncSession | None = None,
    ) -> str:
        prompt = EVENING_CHECK_TEMPLATE.format(**user_data)
        messages = [
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        content, tokens_in, tokens_out = await openai_client.chat_completion(
            messages=messages, temperature=0.7
        )

        if session and user_data.get("user_id"):
            await self._save_analysis(
                session,
                user_id=user_data["user_id"],
                analysis_type=AnalysisType.COACHING_EVENING,
                output=content,
                tokens=tokens_in + tokens_out,
            )

        return content

    async def generate_weekly_summary(
        self,
        user_data: dict,
        session: AsyncSession | None = None,
    ) -> str:
        prompt = WEEKLY_SUMMARY_TEMPLATE.format(**user_data)
        messages = [
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        content, tokens_in, tokens_out = await openai_client.chat_completion(
            messages=messages, temperature=0.6
        )

        if session and user_data.get("user_id"):
            await self._save_analysis(
                session,
                user_id=user_data["user_id"],
                analysis_type=AnalysisType.WEEKLY_SUMMARY,
                output=content,
                tokens=tokens_in + tokens_out,
            )

        return content

    async def assess_weight_progress(self, user_data: dict) -> str:
        prompt = WEIGHT_ASSESSMENT_TEMPLATE.format(**user_data)
        messages = [
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        content, _, _ = await openai_client.chat_completion(messages=messages, temperature=0.5)
        return content

    async def _save_analysis(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        analysis_type: str,
        output: str,
        tokens: int,
    ) -> None:
        try:
            analysis = AIAnalysis(
                user_id=user_id,
                analysis_type=analysis_type,
                output_json={"message": output},
                tokens_used=tokens,
            )
            session.add(analysis)
            await session.flush()
        except Exception as e:
            logger.warning("Failed to save coaching analysis", error=str(e))


ai_coach = AICoach()
