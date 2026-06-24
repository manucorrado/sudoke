"""Baseline schema — users, puzzles, daily puzzles, attempts, audit log.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guest_sessions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("locale", sa.String(16), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
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
    op.create_unique_constraint("uq_guest_sessions_token", "guest_sessions", ["token"])
    op.create_index("ix_guest_sessions_token", "guest_sessions", ["token"])

    user_role = postgresql.ENUM("player", "admin", name="user_role")
    user_role.create(op.get_bind(), checkfirst=True)
    user_role = postgresql.ENUM(
        "player", "admin", name="user_role", create_type=False
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("auth_provider_id", sa.String(255), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("username", sa.String(32), nullable=True),
        sa.Column("display_name", sa.String(64), nullable=True),
        sa.Column("avatar_url", sa.String(1024), nullable=True),
        sa.Column("role", user_role, nullable=False, server_default="player"),
        sa.Column(
            "is_guest", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "claimed_from_guest_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("guest_sessions.id", ondelete="SET NULL"),
            nullable=True,
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
    op.create_unique_constraint("uq_users_auth_provider_id", "users", ["auth_provider_id"])
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.create_index("ix_users_auth_provider_id", "users", ["auth_provider_id"])
    op.create_index("ix_users_username", "users", ["username"])

    op.create_foreign_key(
        "fk_guest_sessions_claimed_by_user_id",
        "guest_sessions",
        "users",
        ["claimed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    puzzle_difficulty = postgresql.ENUM(
        "easy", "medium", "hard", "expert", name="puzzle_difficulty"
    )
    puzzle_difficulty.create(op.get_bind(), checkfirst=True)
    puzzle_difficulty = postgresql.ENUM(
        "easy",
        "medium",
        "hard",
        "expert",
        name="puzzle_difficulty",
        create_type=False,
    )
    puzzle_status = postgresql.ENUM(
        "imported",
        "needs_review",
        "approved",
        "rejected",
        "archived",
        name="puzzle_status",
    )
    puzzle_status.create(op.get_bind(), checkfirst=True)
    puzzle_status = postgresql.ENUM(
        "imported",
        "needs_review",
        "approved",
        "rejected",
        "archived",
        name="puzzle_status",
        create_type=False,
    )

    op.create_table(
        "puzzles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("givens", sa.String(81), nullable=False),
        sa.Column("solution", sa.String(81), nullable=False),
        sa.Column("difficulty", puzzle_difficulty, nullable=False),
        sa.Column(
            "status", puzzle_status, nullable=False, server_default="imported"
        ),
        sa.Column("estimated_min_seconds", sa.Integer(), nullable=False),
        sa.Column("estimated_max_seconds", sa.Integer(), nullable=False),
        sa.Column("clue_count", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("license", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "reviewer_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
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
        sa.CheckConstraint(
            "length(givens) = 81 AND length(solution) = 81",
            name="ck_puzzles_grid_length",
        ),
    )
    op.create_index("ix_puzzles_status", "puzzles", ["status"])
    op.create_index(
        "ix_puzzles_status_difficulty", "puzzles", ["status", "difficulty"]
    )

    daily_puzzle_status = postgresql.ENUM(
        "scheduled",
        "active",
        "finalizing",
        "finalized",
        "cancelled",
        name="daily_puzzle_status",
    )
    daily_puzzle_status.create(op.get_bind(), checkfirst=True)
    daily_puzzle_status = postgresql.ENUM(
        "scheduled",
        "active",
        "finalizing",
        "finalized",
        "cancelled",
        name="daily_puzzle_status",
        create_type=False,
    )

    op.create_table(
        "daily_puzzles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "puzzle_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("puzzles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("scheduled_for", sa.Date(), nullable=False),
        sa.Column("activate_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalize_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            daily_puzzle_status,
            nullable=False,
            server_default="scheduled",
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
        "uq_daily_puzzles_scheduled_for", "daily_puzzles", ["scheduled_for"]
    )
    op.create_index(
        "ix_daily_puzzles_status_scheduled",
        "daily_puzzles",
        ["status", "scheduled_for"],
    )

    attempt_status = postgresql.ENUM(
        "not_started",
        "previewing",
        "started",
        "in_progress",
        "submitted",
        "validated",
        "provisional_ranked",
        "finalized",
        "abandoned",
        "timed_out",
        "invalid",
        "under_review",
        "voided",
        name="attempt_status",
    )
    attempt_status.create(op.get_bind(), checkfirst=True)
    attempt_status = postgresql.ENUM(
        "not_started",
        "previewing",
        "started",
        "in_progress",
        "submitted",
        "validated",
        "provisional_ranked",
        "finalized",
        "abandoned",
        "timed_out",
        "invalid",
        "under_review",
        "voided",
        name="attempt_status",
        create_type=False,
    )

    op.create_table(
        "ranked_attempts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "guest_session_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("guest_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "daily_puzzle_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("daily_puzzles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            attempt_status,
            nullable=False,
            server_default="not_started",
        ),
        sa.Column("previewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abandoned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timed_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mistakes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("official_duration_ms", sa.Integer(), nullable=True),
        sa.Column("under_review_reason", sa.String(64), nullable=True),
        sa.Column("submitted_grid", sa.String(81), nullable=True),
        sa.Column("calculation_version", sa.String(16), nullable=True),
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
        "uq_ranked_attempts_user_daily",
        "ranked_attempts",
        ["user_id", "daily_puzzle_id"],
    )
    op.create_index(
        "ix_ranked_attempts_daily_status",
        "ranked_attempts",
        ["daily_puzzle_id", "status"],
    )

    attempt_event_type = postgresql.ENUM(
        "preview_started",
        "preview_exited",
        "started",
        "place_value",
        "toggle_note",
        "clear_cell",
        "mistake",
        "submitted",
        "validated",
        "abandoned",
        "timed_out",
        "under_review",
        "finalized",
        name="attempt_event_type",
    )
    attempt_event_type.create(op.get_bind(), checkfirst=True)
    attempt_event_type = postgresql.ENUM(
        "preview_started",
        "preview_exited",
        "started",
        "place_value",
        "toggle_note",
        "clear_cell",
        "mistake",
        "submitted",
        "validated",
        "abandoned",
        "timed_out",
        "under_review",
        "finalized",
        name="attempt_event_type",
        create_type=False,
    )

    op.create_table(
        "ranked_attempt_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("ranked_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", attempt_event_type, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("client_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB().with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_ranked_attempt_events_attempt_time",
        "ranked_attempt_events",
        ["attempt_id", "occurred_at"],
    )

    op.create_table(
        "admin_audit_log",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "actor_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=True),
        sa.Column("target_id", sa.String(64), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB().with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_admin_audit_log_action", "admin_audit_log", ["action"])


def downgrade() -> None:
    op.drop_index("ix_admin_audit_log_action", table_name="admin_audit_log")
    op.drop_table("admin_audit_log")
    op.drop_index(
        "ix_ranked_attempt_events_attempt_time", table_name="ranked_attempt_events"
    )
    op.drop_table("ranked_attempt_events")
    op.drop_index("ix_ranked_attempts_daily_status", table_name="ranked_attempts")
    op.drop_constraint("uq_ranked_attempts_user_daily", "ranked_attempts")
    op.drop_table("ranked_attempts")
    op.drop_index("ix_daily_puzzles_status_scheduled", table_name="daily_puzzles")
    op.drop_constraint("uq_daily_puzzles_scheduled_for", "daily_puzzles")
    op.drop_table("daily_puzzles")
    op.drop_index("ix_puzzles_status_difficulty", table_name="puzzles")
    op.drop_index("ix_puzzles_status", table_name="puzzles")
    op.drop_table("puzzles")
    op.drop_constraint("fk_guest_sessions_claimed_by_user_id", "guest_sessions")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_auth_provider_id", table_name="users")
    op.drop_constraint("uq_users_username", "users")
    op.drop_constraint("uq_users_email", "users")
    op.drop_constraint("uq_users_auth_provider_id", "users")
    op.drop_table("users")
    op.drop_index("ix_guest_sessions_token", table_name="guest_sessions")
    op.drop_constraint("uq_guest_sessions_token", "guest_sessions")
    op.drop_table("guest_sessions")

    for enum_name in (
        "attempt_event_type",
        "attempt_status",
        "daily_puzzle_status",
        "puzzle_status",
        "puzzle_difficulty",
        "user_role",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
