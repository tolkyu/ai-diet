import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.food_entry import FoodEntry


class AIAnalysis(Base, UUIDMixin):
    __tablename__ = "ai_analysis"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    food_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("food_entries.id", ondelete="SET NULL")
    )
    food_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("food_logs.id", ondelete="SET NULL")
    )
    analysis_type: Mapped[str] = mapped_column(String(30), nullable=False)
    input_text: Mapped[str | None] = mapped_column(Text)
    input_photo_url: Mapped[str | None] = mapped_column(String(500))
    output_json: Mapped[dict | None] = mapped_column(JSON)
    model_used: Mapped[str | None] = mapped_column(String(50))
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")
