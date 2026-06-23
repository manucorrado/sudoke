"""Social graph + challenge models (Epic 6).

Friendships are modeled as a single directed FriendRequest row that becomes
`accepted` upon mutual approval. For pure friendship list reads the service
treats accepted requests as undirected edges.

Challenges (PRD §16) are share-link records pointing at a daily puzzle (or,
later, an archive puzzle). The challenger publishes one challenge per daily;
recipients are tracked by recording results once they finish.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin, UUIDPrimaryKey


class FriendRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled"


class FriendRequest(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "friend_requests"
    __table_args__ = (
        UniqueConstraint(
            "from_user_id",
            "to_user_id",
            name="uq_friend_requests_pair",
        ),
        CheckConstraint(
            "from_user_id <> to_user_id",
            name="ck_friend_requests_not_self",
        ),
        Index("ix_friend_requests_to_status", "to_user_id", "status"),
        Index("ix_friend_requests_from_status", "from_user_id", "status"),
    )

    from_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    to_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus, name="friend_request_status"),
        default=FriendRequestStatus.pending,
        nullable=False,
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ChallengeStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class Challenge(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "challenges"
    __table_args__ = (
        UniqueConstraint("code", name="uq_challenges_code"),
        Index("ix_challenges_daily", "daily_puzzle_id"),
        Index("ix_challenges_challenger", "challenger_user_id"),
    )

    code: Mapped[str] = mapped_column(String(16), nullable=False)
    challenger_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    daily_puzzle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_puzzles.id", ondelete="CASCADE"), nullable=False
    )
    challenger_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ranked_attempts.id", ondelete="SET NULL"), nullable=True
    )
    challenger_duration_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    challenger_mistakes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[ChallengeStatus] = mapped_column(
        Enum(ChallengeStatus, name="challenge_status"),
        default=ChallengeStatus.active,
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ChallengeAcceptance(UUIDPrimaryKey, TimestampMixin, Base):
    """Records one recipient's outcome for a challenge.

    Either `recipient_user_id` (signed-in) or `recipient_guest_id` (guest)
    is set. Guests can later be claimed; we leave `recipient_user_id` NULL
    until claim time.
    """

    __tablename__ = "challenge_acceptances"
    __table_args__ = (
        Index(
            "ix_challenge_acceptances_challenge",
            "challenge_id",
        ),
        Index(
            "ix_challenge_acceptances_user",
            "recipient_user_id",
        ),
    )

    challenge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False
    )
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    recipient_guest_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="SET NULL"), nullable=True
    )

    attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ranked_attempts.id", ondelete="SET NULL"), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mistakes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


__all__ = [
    "Challenge",
    "ChallengeAcceptance",
    "ChallengeStatus",
    "FriendRequest",
    "FriendRequestStatus",
]
