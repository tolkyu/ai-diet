import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.repositories.subscription import SubscriptionRepository
from app.core.constants import SubscriptionPlan, SubscriptionStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sub_repo = SubscriptionRepository(session)

    async def handle_successful_payment(
        self,
        user_id: uuid.UUID,
        transaction_id: str,
        stars_amount: int,
        plan: str,
        subscription_months: int,
    ) -> Subscription:
        payment = Payment(
            user_id=user_id,
            provider="telegram_stars",
            transaction_id=transaction_id,
            stars_amount=stars_amount,
            plan=plan,
            status="succeeded",
            subscription_months=subscription_months,
        )
        self._session.add(payment)

        sub = await self._sub_repo.get_or_create(user_id)
        now = datetime.now(timezone.utc)

        # If already premium, extend from current expiry; otherwise from now
        if sub.is_premium and sub.expires_at and sub.expires_at > now:
            new_expiry = sub.expires_at + timedelta(days=30 * subscription_months)
        else:
            new_expiry = now + timedelta(days=30 * subscription_months)

        sub = await self._sub_repo.update(
            sub,
            plan=SubscriptionPlan.PREMIUM,
            status=SubscriptionStatus.ACTIVE,
            expires_at=new_expiry,
        )
        await self._session.flush()

        logger.info(
            "Premium activated via Telegram Stars",
            user_id=str(user_id),
            stars=stars_amount,
            plan=plan,
            expires_at=str(new_expiry),
        )
        return sub
