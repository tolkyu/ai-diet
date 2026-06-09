"""Initial migration — creates all tables.

Revision ID: 001
Revises:
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, unique=True, nullable=False),
        sa.Column("username", sa.String(255)),
        sa.Column("first_name", sa.String(255)),
        sa.Column("last_name", sa.String(255)),
        sa.Column("gender", sa.String(10), nullable=False, server_default=""),
        sa.Column("age", sa.Integer),
        sa.Column("height_cm", sa.Numeric(5, 1)),
        sa.Column("weight_kg", sa.Numeric(5, 1)),
        sa.Column("activity_level", sa.String(20), nullable=False, server_default="sedentary"),
        sa.Column("timezone", sa.String(50), server_default="UTC"),
        sa.Column("language_code", sa.String(10), server_default="en"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("is_registered", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "goals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("goal_type", sa.String(20), nullable=False),
        sa.Column("intensity", sa.String(20)),
        sa.Column("target_weight_kg", sa.Numeric(5, 1)),
        sa.Column("target_date", sa.Date),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "daily_targets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("bmr", sa.Numeric(8, 2), nullable=False),
        sa.Column("tdee", sa.Numeric(8, 2), nullable=False),
        sa.Column("calories", sa.Numeric(8, 2), nullable=False),
        sa.Column("protein_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("fat_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("carbs_g", sa.Numeric(8, 2), nullable=False),
        sa.UniqueConstraint("user_id", "date", name="uq_daily_targets_user_date"),
    )

    op.create_table(
        "food_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("total_calories", sa.Numeric(8, 2), server_default="0"),
        sa.Column("total_protein_g", sa.Numeric(8, 2), server_default="0"),
        sa.Column("total_fat_g", sa.Numeric(8, 2), server_default="0"),
        sa.Column("total_carbs_g", sa.Numeric(8, 2), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "date", name="uq_food_log_user_date"),
    )

    op.create_table(
        "food_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("food_log_id", UUID(as_uuid=True), sa.ForeignKey("food_logs.id", ondelete="CASCADE")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("amount_g", sa.Numeric(8, 2)),
        sa.Column("calories", sa.Numeric(8, 2), nullable=False),
        sa.Column("protein_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("fat_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("carbs_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("input_type", sa.String(20), server_default="text"),
        sa.Column("raw_input", sa.Text),
        sa.Column("confidence_score", sa.Numeric(3, 2)),
        sa.Column("source_photo_url", sa.String(500)),
        sa.Column("meal_time", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "weight_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("weight_kg", sa.Numeric(5, 1), nullable=False),
        sa.Column("body_fat_pct", sa.Numeric(4, 1)),
        sa.Column("muscle_mass_kg", sa.Numeric(5, 1)),
        sa.Column("notes", sa.Text),
        sa.Column("measured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "progress_photos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column("s3_url", sa.String(1000)),
        sa.Column("photo_type", sa.String(20), server_default="progress"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("plan", sa.String(20), server_default="free"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("stripe_subscription_id", sa.String(255)),
        sa.Column("daily_text_analyses_used", sa.Integer, server_default="0"),
        sa.Column("daily_photo_analyses_used", sa.Integer, server_default="0"),
        sa.Column("quota_reset_date", sa.Date, server_default=sa.func.current_date()),
    )

    op.create_table(
        "ai_analysis",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("food_entry_id", UUID(as_uuid=True), sa.ForeignKey("food_entries.id", ondelete="SET NULL")),
        sa.Column("food_log_id", UUID(as_uuid=True), sa.ForeignKey("food_logs.id", ondelete="SET NULL")),
        sa.Column("analysis_type", sa.String(30), nullable=False),
        sa.Column("input_text", sa.Text),
        sa.Column("input_photo_url", sa.String(500)),
        sa.Column("output_json", JSONB),
        sa.Column("model_used", sa.String(50)),
        sa.Column("tokens_used", sa.Integer),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("confidence_score", sa.Numeric(3, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("notification_type", sa.String(30), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("is_sent", sa.Boolean, server_default="false"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_id", UUID(as_uuid=True)),
        sa.Column("metadata_json", JSONB),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    tables = [
        "audit_logs", "notifications", "ai_analysis", "subscriptions",
        "progress_photos", "weight_history", "food_entries", "food_logs",
        "daily_targets", "goals", "users",
    ]
    for table in tables:
        op.drop_table(table)
