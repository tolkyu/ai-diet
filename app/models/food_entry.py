import uuid
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.food_log import FoodLog
    from app.models.user import User


class FoodEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "food_entries"

    food_log_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(),
        ForeignKey("food_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    calories: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    carbs_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    input_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)
    raw_input: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    source_photo_url: Mapped[str | None] = mapped_column(String(500))
    meal_time: Mapped[str | None] = mapped_column(String(20))

    food_log: Mapped["FoodLog"] = relationship("FoodLog", back_populates="entries")
    user: Mapped["User"] = relationship("User")
