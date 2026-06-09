import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.weight_history import WeightHistory
from app.repositories.base import BaseRepository


class WeightHistoryRepository(BaseRepository[WeightHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(WeightHistory, session)

    async def get_latest(self, user_id: uuid.UUID) -> WeightHistory | None:
        stmt = (
            select(WeightHistory)
            .where(WeightHistory.user_id == user_id)
            .order_by(WeightHistory.measured_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(self, user_id: uuid.UUID, limit: int = 30) -> list[WeightHistory]:
        stmt = (
            select(WeightHistory)
            .where(WeightHistory.user_id == user_id)
            .order_by(WeightHistory.measured_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
