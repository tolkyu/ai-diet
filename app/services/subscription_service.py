import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import Subscription
from app.repositories.subscription import SubscriptionRepository
from app.core.constants import SubscriptionPlan, SubscriptionStatus
from app.core.config import settings


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.sub_repo = SubscriptionRepository(session)

    async def get_subscription(self, user_id: uuid.UUID) -> Subscription:
        return await self.sub_repo.get_or_create(user_id)

    async def get_usage_info(self, user_id: uuid.UUID, telegram_id: int | None = None) -> dict:
        if telegram_id and telegram_id in settings.admin_telegram_ids_set:
            return {
                "plan": "premium",
                "text_analyses_remaining": "unlimited",
                "photo_analyses_remaining": "unlimited",
            }

        sub = await self.get_subscription(user_id)
        sub = await self.sub_repo.reset_quota_if_needed(sub)

        if sub.is_premium:
            return {
                "plan": "premium",
                "text_analyses_remaining": "unlimited",
                "photo_analyses_remaining": "unlimited",
            }

        return {
            "plan": "free",
            "text_analyses_used": sub.daily_text_analyses_used,
            "text_analyses_limit": settings.free_daily_text_analyses,
            "text_analyses_remaining": max(
                0, settings.free_daily_text_analyses - sub.daily_text_analyses_used
            ),
            "photo_analyses_used": sub.daily_photo_analyses_used,
            "photo_analyses_limit": settings.free_daily_photo_analyses,
            "photo_analyses_remaining": max(
                0, settings.free_daily_photo_analyses - sub.daily_photo_analyses_used
            ),
        }

    async def upgrade_to_premium(self, user_id: uuid.UUID) -> Subscription:
        sub = await self.sub_repo.get_or_create(user_id)
        return await self.sub_repo.update(
            sub,
            plan=SubscriptionPlan.PREMIUM,
            status=SubscriptionStatus.ACTIVE,
        )
