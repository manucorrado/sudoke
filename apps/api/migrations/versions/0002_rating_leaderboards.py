"""Epic 4: rating engine + per-daily leaderboard snapshots.

Revision ID: 0002_rating_leaderboards
Revises: 0001_baseline
Create Date: 2026-06-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_rating_leaderboards"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_ratings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column(
            "provisional_completions",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "last_calculation_version",
            sa.String(16),
            nullable=False,
            server_default="v1",
        ),
        sa.Column(
            "last_finalized_daily_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("daily_puzzles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "last_updated_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_user_ratings_user_id", "user_ratings", ["user_id"]
    )
    op.create_index("ix_user_ratings_user_id", "user_ratings", ["user_id"])

    op.create_table(
        "rating_history",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "daily_puzzle_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("daily_puzzles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("ranked_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "kind", sa.String(16), nullable=False, server_default="projected"
        ),
        sa.Column("old_rating", sa.Integer(), nullable=False),
        sa.Column("new_rating", sa.Integer(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("percentile", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "cohort_size", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "was_provisional",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "calculation_version",
            sa.String(16),
            nullable=False,
            server_default="v1",
        ),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint(
        "uq_rating_history_user_daily_kind",
        "rating_history",
        ["user_id", "daily_puzzle_id", "kind"],
    )
    op.create_index(
        "ix_rating_history_user_applied",
        "rating_history",
        ["user_id", "applied_at"],
    )
    op.create_index(
        "ix_rating_history_daily",
        "rating_history",
        ["daily_puzzle_id"],
    )

    op.create_table(
        "daily_results",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "daily_puzzle_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("daily_puzzles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("ranked_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("cohort_size", sa.Integer(), nullable=False),
        sa.Column("percentile", sa.Numeric(5, 2), nullable=False),
        sa.Column("mistakes", sa.Integer(), nullable=False),
        sa.Column("official_duration_ms", sa.Integer(), nullable=False),
        sa.Column("rating_before", sa.Integer(), nullable=False),
        sa.Column("rating_after", sa.Integer(), nullable=False),
        sa.Column("rating_delta", sa.Integer(), nullable=False),
        sa.Column(
            "was_provisional",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "calculation_version",
            sa.String(16),
            nullable=False,
            server_default="v1",
        ),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_daily_results_user_daily",
        "daily_results",
        ["user_id", "daily_puzzle_id"],
    )
    op.create_index(
        "ix_daily_results_daily_duration",
        "daily_results",
        ["daily_puzzle_id", "official_duration_ms"],
    )


def downgrade() -> None:
    op.drop_index("ix_daily_results_daily_duration", table_name="daily_results")
    op.drop_constraint("uq_daily_results_user_daily", "daily_results")
    op.drop_table("daily_results")

    op.drop_index("ix_rating_history_daily", table_name="rating_history")
    op.drop_index("ix_rating_history_user_applied", table_name="rating_history")
    op.drop_constraint(
        "uq_rating_history_user_daily_kind", "rating_history"
    )
    op.drop_table("rating_history")

    op.drop_index("ix_user_ratings_user_id", table_name="user_ratings")
    op.drop_constraint("uq_user_ratings_user_id", "user_ratings")
    op.drop_table("user_ratings")
