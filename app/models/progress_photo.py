import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class ProgressPhoto(Base, UUIDMixin):
    __tablename__ = "progress_photos"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_url: Mapped[str | None] = mapped_column(String(1000))
    photo_type: Mapped[str] = mapped_column(String(20), default="progress", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")
