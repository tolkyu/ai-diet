import uuid
from decimal import Decimal
from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Goal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    goal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    intensity: Mapped[str | None] = mapped_column(String(20))
    target_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    target_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="goals")

    def __repr__(self) -> str:
        return f"<Goal user_id={self.user_id} type={self.goal_type} active={self.is_active}>"
