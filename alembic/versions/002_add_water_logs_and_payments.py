"""Add water_logs and payments tables.

Revision ID: 002
Revises: 001
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "water_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("total_ml", sa.Integer, nullable=False, server_default="0"),
        sa.Column("goal_ml", sa.Integer, nullable=False, server_default="2000"),
        sa.UniqueConstraint("user_id", "date", name="uq_water_log_user_date"),
    )

    op.create_table(
        "payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider", sa.String(30), nullable=False, server_default="telegram_stars"),
        sa.Column("transaction_id", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("stars_amount", sa.Integer, nullable=False),
        sa.Column("plan", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="succeeded"),
        sa.Column("subscription_months", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("water_logs")
