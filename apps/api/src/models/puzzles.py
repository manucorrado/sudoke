from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, UUIDPrimaryKey


class PuzzleDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
    expert = "expert"


class PuzzleStatus(str, enum.Enum):
    imported = "imported"
    needs_review = "needs_review"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"


class DailyPuzzleStatus(str, enum.Enum):
    scheduled = "scheduled"
    active = "active"
    finalizing = "finalizing"
    finalized = "finalized"
    cancelled = "cancelled"


class Puzzle(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "puzzles"
    __table_args__ = (
        CheckConstraint(
            "length(givens) = 81 AND length(solution) = 81",
            name="ck_puzzles_grid_length",
        ),
        Index("ix_puzzles_status_difficulty", "status", "difficulty"),
    )

    givens: Mapped[str] = mapped_column(String(81), nullable=False)
    solution: Mapped[str] = mapped_column(String(81), nullable=False)
    difficulty: Mapped[PuzzleDifficulty] = mapped_column(
        Enum(PuzzleDifficulty, name="puzzle_difficulty"), nullable=False
    )
    status: Mapped[PuzzleStatus] = mapped_column(
        Enum(PuzzleStatus, name="puzzle_status"),
        default=PuzzleStatus.imported,
        nullable=False,
        index=True,
    )

    estimated_min_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_max_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    clue_count: Mapped[int] = mapped_column(Integer, nullable=False)

    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    license: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    daily_puzzles: Mapped[list[DailyPuzzle]] = relationship(
        back_populates="puzzle", lazy="raise"
    )


class DailyPuzzle(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "daily_puzzles"
    __table_args__ = (
        UniqueConstraint("scheduled_for", name="uq_daily_puzzles_scheduled_for"),
        Index("ix_daily_puzzles_status_scheduled", "status", "scheduled_for"),
    )

    puzzle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("puzzles.id", ondelete="RESTRICT"), nullable=False
    )
    scheduled_for: Mapped[date] = mapped_column(Date, nullable=False)
    activate_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalize_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[DailyPuzzleStatus] = mapped_column(
        Enum(DailyPuzzleStatus, name="daily_puzzle_status"),
        default=DailyPuzzleStatus.scheduled,
        nullable=False,
    )

    puzzle: Mapped[Puzzle] = relationship(back_populates="daily_puzzles", lazy="joined")
