import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class WeightHistory(Base, UUIDMixin):
    __tablename__ = "weight_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    body_fat_pct: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    muscle_mass_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    notes: Mapped[str | None] = mapped_column(Text)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="weight_history")
