import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.water_log import WaterLog


class WaterService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_today_log(self, user_id: uuid.UUID) -> WaterLog:
        today = date.today()
        result = await self._session.execute(
            select(WaterLog).where(WaterLog.user_id == user_id, WaterLog.date == today)
        )
        log = result.scalar_one_or_none()
        if not log:
            log = WaterLog(user_id=user_id, date=today, total_ml=0, goal_ml=2000)
            self._session.add(log)
            await self._session.flush()
        return log

    async def add_water(self, user_id: uuid.UUID, ml: int) -> WaterLog:
        log = await self.get_today_log(user_id)
        log.total_ml += ml
        await self._session.flush()
        return log

    async def set_goal(self, user_id: uuid.UUID, goal_ml: int) -> WaterLog:
        log = await self.get_today_log(user_id)
        log.goal_ml = goal_ml
        await self._session.flush()
        return log
