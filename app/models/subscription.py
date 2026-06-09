import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, UUIDMixin
from app.core.constants import SubscriptionPlan, SubscriptionStatus

if TYPE_CHECKING:
    from app.models.user import User


class Subscription(Base, UUIDMixin):
    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    plan: Mapped[str] = mapped_column(
        String(20), default=SubscriptionPlan.FREE, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=SubscriptionStatus.ACTIVE, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Future Stripe integration fields
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))

    # Daily quota tracking
    daily_text_analyses_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_photo_analyses_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quota_reset_date: Mapped[date] = mapped_column(
        Date, default=date.today, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="subscription")

    @property
    def is_premium(self) -> bool:
        return self.plan == SubscriptionPlan.PREMIUM and self.status == SubscriptionStatus.ACTIVE
