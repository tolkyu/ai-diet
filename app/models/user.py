import uuid
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDMixin
from app.core.constants import ActivityLevel, Gender

if TYPE_CHECKING:
    from app.models.goal import Goal
    from app.models.food_log import FoodLog
    from app.models.weight_history import WeightHistory
    from app.models.subscription import Subscription
    from app.models.notification import Notification
    from app.models.audit_log import AuditLog
    from app.models.payment import Payment
    from app.models.water_log import WaterLog


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))

    # Physical attributes (required for calculations)
    gender: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    age: Mapped[int | None] = mapped_column()
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    activity_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ActivityLevel.SEDENTARY
    )

    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    goals: Mapped[list["Goal"]] = relationship(
        "Goal", back_populates="user", cascade="all, delete-orphan"
    )
    food_logs: Mapped[list["FoodLog"]] = relationship(
        "FoodLog", back_populates="user", cascade="all, delete-orphan"
    )
    weight_history: Mapped[list["WeightHistory"]] = relationship(
        "WeightHistory", back_populates="user", cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="user", cascade="all, delete-orphan"
    )
    water_logs: Mapped[list["WaterLog"]] = relationship(
        "WaterLog", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def display_name(self) -> str:
        if self.first_name:
            return self.first_name
        if self.username:
            return f"@{self.username}"
        return f"User {self.telegram_id}"

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} name={self.display_name}>"
