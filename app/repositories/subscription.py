import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository
from app.core.constants import SubscriptionPlan, SubscriptionStatus


class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Subscription, session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: uuid.UUID) -> Subscription:
        sub = await self.get_by_user_id(user_id)
        if sub:
            return sub
        return await self.create(user_id=user_id)

    async def reset_quota_if_needed(self, sub: Subscription) -> Subscription:
        today = date.today()
        if sub.quota_reset_date < today:
            sub.daily_text_analyses_used = 0
            sub.daily_photo_analyses_used = 0
            sub.quota_reset_date = today
            self.session.add(sub)
            await self.session.flush()
        return sub
