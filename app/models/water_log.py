import uuid
from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class WaterLog(Base, UUIDMixin):
    __tablename__ = "water_logs"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_water_log_user_date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_ml: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    goal_ml: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)

    user: Mapped["User"] = relationship("User", back_populates="water_logs")
