"""Streak + freeze logic (PRD §18, Epic 8).

Rules:
    - Streak extends when a user records an *official* daily ranked
      completion within the daily window (caller passes the date the
      completion belongs to).
    - On a missed day, a single freeze is auto-consumed (if held).
    - 1 freeze is earned per `FREEZES_PER_COMPLETIONS` official
      completions; capped at `MAX_FREEZES_HELD`.
    - Freezes cannot be purchased and never gate ranked play.

The service is idempotent per (user, day): calling
`record_completion` twice for the same calendar day no-ops on the
second call. Tests pin `today` so the logic is timezone-stable.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import NotificationPreference, User, UserStreak

MAX_FREEZES_HELD = 2
FREEZES_PER_COMPLETIONS = 7


async def get_or_create_streak(
    session: AsyncSession, user: User
) -> UserStreak:
    result = await session.execute(
        select(UserStreak).where(UserStreak.user_id == user.id)
    )
    streak = result.scalar_one_or_none()
    if streak is not None:
        return streak
    streak = UserStreak(user_id=user.id)
    session.add(streak)
    await session.flush()
    return streak


def _apply_missed_days(streak: UserStreak, today: date) -> None:
    """Auto-consume freezes for days missed before `today`.

    If we still have a gap after spending available freezes, the streak
    breaks (reset to 0).
    """

    if streak.last_completed_date is None:
        return
    missed = (today - streak.last_completed_date).days - 1
    if missed <= 0:
        return
    spendable = min(missed, streak.freezes_held)
    if spendable > 0:
        streak.freezes_held -= spendable
        streak.last_freeze_consumed_at = datetime.now(timezone.utc)
    remaining_missed = missed - spendable
    if remaining_missed > 0:
        streak.current_length = 0
        streak.streak_started_date = None


async def record_completion(
    session: AsyncSession, user: User, *, completed_on: date
) -> UserStreak:
    """Idempotent: extends the streak for the given completion date."""

    streak = await get_or_create_streak(session, user)

    if (
        streak.last_completed_date is not None
        and streak.last_completed_date >= completed_on
    ):
        return streak

    _apply_missed_days(streak, completed_on)

    if (
        streak.last_completed_date is not None
        and streak.last_completed_date == completed_on - timedelta(days=1)
    ):
        streak.current_length += 1
    elif streak.current_length == 0:
        streak.current_length = 1
        streak.streak_started_date = completed_on
    else:
        # Gap was covered entirely by freezes — continue the streak.
        streak.current_length += 1

    streak.last_completed_date = completed_on
    if streak.streak_started_date is None:
        streak.streak_started_date = completed_on
    if streak.current_length > streak.longest_length:
        streak.longest_length = streak.current_length

    streak.completions_total += 1
    streak.completions_since_last_freeze += 1
    if streak.completions_since_last_freeze >= FREEZES_PER_COMPLETIONS:
        earned = streak.completions_since_last_freeze // FREEZES_PER_COMPLETIONS
        streak.completions_since_last_freeze = (
            streak.completions_since_last_freeze % FREEZES_PER_COMPLETIONS
        )
        before = streak.freezes_held
        streak.freezes_held = min(MAX_FREEZES_HELD, before + earned)
        streak.freezes_earned += streak.freezes_held - before

    return streak


async def sync_to_today(
    session: AsyncSession, user: User, *, today: date
) -> UserStreak:
    """Apply any missed-day freeze consumption up to `today`.

    Called on read so the displayed `current_length` always reflects
    missed days. Idempotent.
    """

    streak = await get_or_create_streak(session, user)
    if streak.last_completed_date is None:
        return streak
    if today <= streak.last_completed_date:
        return streak
    _apply_missed_days(streak, today)
    return streak


async def get_or_create_notification_preferences(
    session: AsyncSession, user: User
) -> NotificationPreference:
    result = await session.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user.id
        )
    )
    prefs = result.scalar_one_or_none()
    if prefs is not None:
        return prefs
    prefs = NotificationPreference(user_id=user.id)
    session.add(prefs)
    await session.flush()
    return prefs


__all__ = [
    "FREEZES_PER_COMPLETIONS",
    "MAX_FREEZES_HELD",
    "get_or_create_notification_preferences",
    "get_or_create_streak",
    "record_completion",
    "sync_to_today",
]
