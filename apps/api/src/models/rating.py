"""Rating and rating history models (PRD §14).

A `UserRating` row stores each player's current rating (starts at 1000),
provisional-completion count, and the calculation version it was produced
with. `RatingHistory` is append-only — every projected or finalized delta
writes a row so we can rebuild the rating from scratch and surface a
history view on the Profile tab.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin, UUIDPrimaryKey


class UserRating(UUIDPrimaryKey, TimestampMixin, Base):
    """Current rating snapshot for a user. One row per user."""

    __tablename__ = "user_ratings"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_ratings_user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Stored as integer (whole-point rating).
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    # Count of valid completions; first 10 are provisional (§14.6).
    provisional_completions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_calculation_version: Mapped[str] = mapped_column(
        String(16), nullable=False, default="v1"
    )
    last_finalized_daily_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("daily_puzzles.id", ondelete="SET NULL"), nullable=True
    )
    last_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RatingHistory(UUIDPrimaryKey, Base):
    """Append-only history of rating changes.

    Rows are written in two places:
    - Projected entry right after `submit_attempt` lands a valid solve.
    - Final entry by `finalize_daily_ratings` when the daily window closes.
    """

    __tablename__ = "rating_history"
    __table_args__ = (
        Index("ix_rating_history_user_applied", "user_id", "applied_at"),
        Index("ix_rating_history_daily", "daily_puzzle_id"),
        UniqueConstraint(
            "user_id", "daily_puzzle_id", "kind",
            name="uq_rating_history_user_daily_kind",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    daily_puzzle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_puzzles.id", ondelete="CASCADE"), nullable=False
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ranked_attempts.id", ondelete="CASCADE"), nullable=False
    )

    # "projected" written on submit; "final" written by daily finalization job.
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="projected")

    old_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    new_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)

    # Percentile in 0..100 (decimal precision for analytics).
    percentile: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    cohort_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    was_provisional: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    calculation_version: Mapped[str] = mapped_column(
        String(16), nullable=False, default="v1"
    )

    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class DailyResult(UUIDPrimaryKey, TimestampMixin, Base):
    """Per-user, per-daily finalized result snapshot.

    Written by the daily-finalization job once the cohort is closed. Powers
    historical leaderboards and `/daily/{id}/my-result` after close.
    """

    __tablename__ = "daily_results"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "daily_puzzle_id", name="uq_daily_results_user_daily"
        ),
        Index(
            "ix_daily_results_daily_duration", "daily_puzzle_id", "official_duration_ms"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    daily_puzzle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_puzzles.id", ondelete="CASCADE"), nullable=False
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ranked_attempts.id", ondelete="CASCADE"), nullable=False
    )

    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    cohort_size: Mapped[int] = mapped_column(Integer, nullable=False)
    percentile: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    mistakes: Mapped[int] = mapped_column(Integer, nullable=False)
    official_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    rating_before: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_after: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    was_provisional: Mapped[bool] = mapped_column(default=False, nullable=False)
    calculation_version: Mapped[str] = mapped_column(
        String(16), nullable=False, default="v1"
    )

    finalized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


__all__ = ["UserRating", "RatingHistory", "DailyResult"]
