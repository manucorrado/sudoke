"""Epics 6 + 8 — social graph, challenges, streaks, notification prefs.

Revision ID: 0003_social_streaks
Revises: 0002_rating_leaderboards
Create Date: 2026-06-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_social_streaks"
down_revision = "0002_rating_leaderboards"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_streaks",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("current_length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("longest_length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_completed_date", sa.Date(), nullable=True),
        sa.Column("streak_started_date", sa.Date(), nullable=True),
        sa.Column("freezes_held", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("freezes_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "completions_total", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "completions_since_last_freeze",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "last_freeze_consumed_at",
            sa.DateTime(timezone=True),
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
    op.create_unique_constraint(
        "uq_user_streaks_user_id", "user_streaks", ["user_id"]
    )
    op.create_index("ix_user_streaks_user_id", "user_streaks", ["user_id"])

    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "daily_reminder",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "friend_challenged_you",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "beat_your_time",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "final_ranking_ready",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
        "uq_notification_preferences_user_id",
        "notification_preferences",
        ["user_id"],
    )
    op.create_index(
        "ix_notification_preferences_user_id",
        "notification_preferences",
        ["user_id"],
    )

    friend_request_status = postgresql.ENUM(
        "pending",
        "accepted",
        "declined",
        "cancelled",
        name="friend_request_status",
    )
    friend_request_status.create(op.get_bind(), checkfirst=True)
    friend_request_status = postgresql.ENUM(
        "pending",
        "accepted",
        "declined",
        "cancelled",
        name="friend_request_status",
        create_type=False,
    )

    op.create_table(
        "friend_requests",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "from_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            friend_request_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "responded_at", sa.DateTime(timezone=True), nullable=True
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
        sa.UniqueConstraint(
            "from_user_id", "to_user_id", name="uq_friend_requests_pair"
        ),
        sa.CheckConstraint(
            "from_user_id <> to_user_id",
            name="ck_friend_requests_not_self",
        ),
    )
    op.create_index(
        "ix_friend_requests_to_status",
        "friend_requests",
        ["to_user_id", "status"],
    )
    op.create_index(
        "ix_friend_requests_from_status",
        "friend_requests",
        ["from_user_id", "status"],
    )

    challenge_status = postgresql.ENUM(
        "active", "expired", "cancelled", name="challenge_status"
    )
    challenge_status.create(op.get_bind(), checkfirst=True)
    challenge_status = postgresql.ENUM(
        "active", "expired", "cancelled", name="challenge_status", create_type=False
    )

    op.create_table(
        "challenges",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column(
            "challenger_user_id",
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
            "challenger_attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("ranked_attempts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("challenger_duration_ms", sa.Integer(), nullable=True),
        sa.Column("challenger_mistakes", sa.Integer(), nullable=True),
        sa.Column(
            "status", challenge_status, nullable=False, server_default="active"
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
        "uq_challenges_code", "challenges", ["code"]
    )
    op.create_index(
        "ix_challenges_daily", "challenges", ["daily_puzzle_id"]
    )
    op.create_index(
        "ix_challenges_challenger", "challenges", ["challenger_user_id"]
    )

    op.create_table(
        "challenge_acceptances",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "challenge_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("challenges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recipient_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "recipient_guest_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("guest_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "attempt_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("ranked_attempts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("mistakes", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index(
        "ix_challenge_acceptances_challenge",
        "challenge_acceptances",
        ["challenge_id"],
    )
    op.create_index(
        "ix_challenge_acceptances_user",
        "challenge_acceptances",
        ["recipient_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_challenge_acceptances_user", table_name="challenge_acceptances"
    )
    op.drop_index(
        "ix_challenge_acceptances_challenge", table_name="challenge_acceptances"
    )
    op.drop_table("challenge_acceptances")

    op.drop_index("ix_challenges_challenger", table_name="challenges")
    op.drop_index("ix_challenges_daily", table_name="challenges")
    op.drop_constraint("uq_challenges_code", "challenges")
    op.drop_table("challenges")
    sa.Enum(name="challenge_status").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_friend_requests_from_status", table_name="friend_requests")
    op.drop_index("ix_friend_requests_to_status", table_name="friend_requests")
    op.drop_table("friend_requests")
    sa.Enum(name="friend_request_status").drop(op.get_bind(), checkfirst=True)

    op.drop_index(
        "ix_notification_preferences_user_id",
        table_name="notification_preferences",
    )
    op.drop_constraint(
        "uq_notification_preferences_user_id", "notification_preferences"
    )
    op.drop_table("notification_preferences")

    op.drop_index("ix_user_streaks_user_id", table_name="user_streaks")
    op.drop_constraint("uq_user_streaks_user_id", "user_streaks")
    op.drop_table("user_streaks")
