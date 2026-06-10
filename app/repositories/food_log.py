import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.food_log import FoodLog
from app.models.food_entry import FoodEntry
from app.repositories.base import BaseRepository


class FoodLogRepository(BaseRepository[FoodLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(FoodLog, session)

    async def get_by_user_and_date(self, user_id: uuid.UUID, log_date: date) -> FoodLog | None:
        stmt = (
            select(FoodLog)
            .where(FoodLog.user_id == user_id, FoodLog.date == log_date)
            .options(selectinload(FoodLog.entries))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_for_date(self, user_id: uuid.UUID, log_date: date) -> FoodLog:
        log = await self.get_by_user_and_date(user_id, log_date)
        if log:
            return log
        return await self.create(user_id=user_id, date=log_date)

    async def get_recent_logs(self, user_id: uuid.UUID, days: int = 7) -> list[FoodLog]:
        from sqlalchemy import func, text
        stmt = (
            select(FoodLog)
            .where(FoodLog.user_id == user_id)
            .order_by(FoodLog.date.desc())
            .limit(days)
            .options(selectinload(FoodLog.entries))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def recalculate_totals(self, food_log_id: uuid.UUID) -> None:
        from sqlalchemy import func, update
        subq = (
            select(
                func.coalesce(func.sum(FoodEntry.calories), 0).label("cal"),
                func.coalesce(func.sum(FoodEntry.protein_g), 0).label("prot"),
                func.coalesce(func.sum(FoodEntry.fat_g), 0).label("fat"),
                func.coalesce(func.sum(FoodEntry.carbs_g), 0).label("carbs"),
            )
            .where(FoodEntry.food_log_id == food_log_id)
            .scalar_subquery()
        )
        # Reload and update
        log = await self.get_or_raise(food_log_id)
        entries_stmt = select(FoodEntry).where(FoodEntry.food_log_id == food_log_id)
        entries_result = await self.session.execute(entries_stmt)
        entries = list(entries_result.scalars().all())

        log.total_calories = sum(float(e.calories) for e in entries)
        log.total_protein_g = sum(float(e.protein_g) for e in entries)
        log.total_fat_g = sum(float(e.fat_g) for e in entries)
        log.total_carbs_g = sum(float(e.carbs_g) for e in entries)
        self.session.add(log)
        await self.session.flush()
