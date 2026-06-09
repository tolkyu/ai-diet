import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDType, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base, UUIDMixin):
    """Immutable audit trail — never updated, only inserted."""
    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType())
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
