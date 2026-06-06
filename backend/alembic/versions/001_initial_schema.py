"""Initial schema: users, ssi_snapshots, recommendations, report_history, scraping_runs

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("linkedin_username_enc", sa.String(1024), nullable=False, server_default=""),
        sa.Column("linkedin_password_enc", sa.String(1024), nullable=False, server_default=""),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ai_provider", sa.String(32), nullable=False, server_default="openai"),
        sa.Column("notify_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── scraping_runs ──────────────────────────────────────────────────────────
    op.create_table(
        "scraping_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trigger", sa.String(32), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scraping_runs_id", "scraping_runs", ["id"])
    op.create_index("ix_scraping_runs_user_id", "scraping_runs", ["user_id"])

    # ── ssi_snapshots ──────────────────────────────────────────────────────────
    op.create_table(
        "ssi_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scraping_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("professional_brand_score", sa.Float(), nullable=False),
        sa.Column("find_right_people_score", sa.Float(), nullable=False),
        sa.Column("engage_with_insights_score", sa.Float(), nullable=False),
        sa.Column("build_relationships_score", sa.Float(), nullable=False),
        sa.Column("industry_avg_score", sa.Float(), nullable=True),
        sa.Column("network_avg_score", sa.Float(), nullable=True),
        sa.Column("screenshot_path", sa.String(512), nullable=True),
        sa.Column("raw_html_path", sa.String(512), nullable=True),
        sa.Column("delta_1d", sa.Float(), nullable=True),
        sa.Column("delta_7d", sa.Float(), nullable=True),
        sa.Column("delta_30d", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scraping_run_id"], ["scraping_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ssi_snapshots_id", "ssi_snapshots", ["id"])
    op.create_index("ix_ssi_snapshots_user_id", "ssi_snapshots", ["user_id"])
    op.create_index("ix_ssi_snapshots_snapshot_date", "ssi_snapshots", ["snapshot_date"])

    # ── recommendations ────────────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("expected_impact", sa.Text(), nullable=False),
        sa.Column("action_steps", sa.Text(), nullable=True),
        sa.Column("ai_provider", sa.String(32), nullable=False, server_default="openai"),
        sa.Column("ai_model", sa.String(64), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["ssi_snapshots.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recommendations_id", "recommendations", ["id"])
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])
    op.create_index("ix_recommendations_snapshot_id", "recommendations", ["snapshot_id"])

    # ── report_history ─────────────────────────────────────────────────────────
    op.create_table(
        "report_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_type", sa.String(32), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("email_sent_to", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_history_id", "report_history", ["id"])
    op.create_index("ix_report_history_user_id", "report_history", ["user_id"])
    op.create_index("ix_report_history_report_date", "report_history", ["report_date"])


def downgrade() -> None:
    op.drop_table("report_history")
    op.drop_table("recommendations")
    op.drop_table("ssi_snapshots")
    op.drop_table("scraping_runs")
    op.drop_table("users")
