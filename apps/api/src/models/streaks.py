"""Streak + notification preference models (Epic 8).

Streaks (PRD §18):
    - extends on official daily completion within the global window
    - up to 2 freezes, auto-consumed on missed day
    - earn 1 freeze per 7 official completions (no purchase/ads)

Notification preferences (PRD §19):
    - per-channel boolean toggles
    - persistence is enough for now; push delivery is post-MVP infra
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin, UUIDPrimaryKey


class UserStreak(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "user_streaks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    current_length: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_length: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    streak_started_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    freezes_held: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    freezes_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    completions_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completions_since_last_freeze: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    last_freeze_consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class NotificationPreference(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    daily_reminder: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    friend_challenged_you: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    beat_your_time: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    final_ranking_ready: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


__all__ = ["NotificationPreference", "UserStreak"]
