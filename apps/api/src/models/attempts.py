from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from src.db.base import Base, TimestampMixin, UUIDPrimaryKey


class AttemptStatus(str, enum.Enum):
    not_started = "not_started"
    previewing = "previewing"
    started = "started"
    in_progress = "in_progress"
    submitted = "submitted"
    validated = "validated"
    provisional_ranked = "provisional_ranked"
    finalized = "finalized"
    abandoned = "abandoned"
    timed_out = "timed_out"
    invalid = "invalid"
    under_review = "under_review"
    voided = "voided"


TERMINAL_STATUSES: frozenset[AttemptStatus] = frozenset(
    {
        AttemptStatus.finalized,
        AttemptStatus.abandoned,
        AttemptStatus.timed_out,
        AttemptStatus.invalid,
        AttemptStatus.voided,
    }
)


class AttemptEventType(str, enum.Enum):
    preview_started = "preview_started"
    preview_exited = "preview_exited"
    started = "started"
    place_value = "place_value"
    toggle_note = "toggle_note"
    clear_cell = "clear_cell"
    mistake = "mistake"
    submitted = "submitted"
    validated = "validated"
    abandoned = "abandoned"
    timed_out = "timed_out"
    under_review = "under_review"
    finalized = "finalized"


# JSONB on Postgres, JSON elsewhere (sqlite tests).
JSONColumn = JSONB().with_variant(JSON(), "sqlite")


class RankedAttempt(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "ranked_attempts"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "daily_puzzle_id", name="uq_ranked_attempts_user_daily"
        ),
        Index("ix_ranked_attempts_daily_status", "daily_puzzle_id", "status"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    guest_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="SET NULL"), nullable=True
    )
    daily_puzzle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_puzzles.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, name="attempt_status"),
        default=AttemptStatus.not_started,
        nullable=False,
    )

    previewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    abandoned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timed_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    mistakes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    official_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Conservative anti-cheat flag — see §26.
    under_review_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Snapshot of submitted final grid for auditability (81 chars).
    submitted_grid: Mapped[str | None] = mapped_column(String(81), nullable=True)

    # Rating-engine bookkeeping (Epic 4 will populate).
    calculation_version: Mapped[str | None] = mapped_column(String(16), nullable=True)

    events: Mapped[list[RankedAttemptEvent]] = relationship(
        back_populates="attempt",
        order_by="RankedAttemptEvent.occurred_at",
        cascade="all, delete-orphan",
        lazy="raise",
    )


class RankedAttemptEvent(UUIDPrimaryKey, Base):
    __tablename__ = "ranked_attempt_events"
    __table_args__ = (
        Index("ix_ranked_attempt_events_attempt_time", "attempt_id", "occurred_at"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ranked_attempts.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[AttemptEventType] = mapped_column(
        Enum(AttemptEventType, name="attempt_event_type"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # Client-reported timestamp — may differ from `occurred_at` (server clock).
    client_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict | None] = mapped_column(JSONColumn, nullable=True)

    attempt: Mapped[RankedAttempt] = relationship(back_populates="events", lazy="raise")
