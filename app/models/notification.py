import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_type: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship("User", back_populates="notifications")
