import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class DailyTargets(Base, UUIDMixin):
    __tablename__ = "daily_targets"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_daily_targets_user_date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)

    bmr: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    tdee: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    calories: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    carbs_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    user: Mapped["User"] = relationship("User")
