import uuid
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.food_log import FoodLog
from app.models.food_entry import FoodEntry
from app.repositories.food_log import FoodLogRepository
from app.repositories.subscription import SubscriptionRepository
from app.core.exceptions import QuotaExceededError
from app.core.constants import FoodInputType, SubscriptionPlan
from app.core.config import settings


class FoodLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.food_log_repo = FoodLogRepository(session)
        self.sub_repo = SubscriptionRepository(session)

    async def check_and_increment_quota(
        self, user_id: uuid.UUID, input_type: FoodInputType
    ) -> None:
        sub = await self.sub_repo.get_or_create(user_id)
        sub = await self.sub_repo.reset_quota_if_needed(sub)

        if sub.is_premium:
            return  # no limits

        if input_type == FoodInputType.PHOTO:
            limit = settings.free_daily_photo_analyses
            if sub.daily_photo_analyses_used >= limit:
                raise QuotaExceededError("photo analyses", limit)
            sub.daily_photo_analyses_used += 1
        else:
            limit = settings.free_daily_text_analyses
            if sub.daily_text_analyses_used >= limit:
                raise QuotaExceededError("text analyses", limit)
            sub.daily_text_analyses_used += 1

        self.session.add(sub)
        await self.session.flush()

    async def add_food_entries(
        self,
        user_id: uuid.UUID,
        entries_data: list[dict],
        input_type: str = FoodInputType.TEXT,
        raw_input: str | None = None,
        log_date: date | None = None,
    ) -> tuple[FoodLog, list[FoodEntry]]:
        log_date = log_date or date.today()
        food_log = await self.food_log_repo.get_or_create_for_date(user_id, log_date)

        created_entries = []
        for entry_data in entries_data:
            entry = FoodEntry(
                food_log_id=food_log.id,
                user_id=user_id,
                name=entry_data["name"],
                amount_g=entry_data.get("amount_g"),
                calories=entry_data["calories"],
                protein_g=entry_data["protein_g"],
                fat_g=entry_data["fat_g"],
                carbs_g=entry_data["carbs_g"],
                input_type=input_type,
                raw_input=raw_input,
                confidence_score=entry_data.get("confidence_score"),
                source_photo_url=entry_data.get("source_photo_url"),
                meal_time=entry_data.get("meal_time"),
            )
            self.session.add(entry)
            created_entries.append(entry)

        await self.session.flush()
        await self.food_log_repo.recalculate_totals(food_log.id)
        await self.session.refresh(food_log)
        return food_log, created_entries

    async def get_today_log(self, user_id: uuid.UUID) -> FoodLog | None:
        return await self.food_log_repo.get_by_user_and_date(user_id, date.today())

    async def get_recent_logs(self, user_id: uuid.UUID, days: int = 7) -> list[FoodLog]:
        return await self.food_log_repo.get_recent_logs(user_id, days)

    async def delete_entry(self, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        from sqlalchemy import select
        from app.models.food_entry import FoodEntry
        stmt = select(FoodEntry).where(
            FoodEntry.id == entry_id, FoodEntry.user_id == user_id
        )
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()
        if not entry:
            return
        food_log_id = entry.food_log_id
        await self.session.delete(entry)
        await self.session.flush()
        await self.food_log_repo.recalculate_totals(food_log_id)
