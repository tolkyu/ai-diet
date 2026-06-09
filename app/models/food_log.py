import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.food_entry import FoodEntry


class FoodLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "food_logs"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_food_log_user_date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)

    total_calories: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    total_protein_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    total_fat_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    total_carbs_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)

    user: Mapped["User"] = relationship("User", back_populates="food_logs")
    entries: Mapped[list["FoodEntry"]] = relationship(
        "FoodEntry", back_populates="food_log", cascade="all, delete-orphan"
    )
