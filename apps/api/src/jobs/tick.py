"""One-shot job tick used by the cron worker.

Order of operations matters: we activate first so any newly-due daily is
visible to clients, then time-out attempts whose window has just closed,
then finalize ratings for daily puzzles that have crossed `finalize_at`.

Idempotent end-to-end — safe to call multiple times per minute.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import DailyPuzzle, DailyPuzzleStatus
from src.services.attempts import timeout_due_attempts
from src.services.puzzles import (
    activate_due_daily_puzzles,
    finalize_due_daily_puzzles,
)
from src.services.rating import finalize_daily_ratings


@dataclass
class JobReport:
    activated: list[uuid.UUID] = field(default_factory=list)
    timed_out_attempts: list[uuid.UUID] = field(default_factory=list)
    finalized_dailies: list[uuid.UUID] = field(default_factory=list)
    rated_attempts: int = 0


async def run_due_jobs(
    session: AsyncSession, *, now: datetime | None = None
) -> JobReport:
    moment = now or datetime.now(timezone.utc)
    report = JobReport()

    report.activated = await activate_due_daily_puzzles(session, now=moment)
    report.timed_out_attempts = await timeout_due_attempts(session, now=moment)
    report.finalized_dailies = await finalize_due_daily_puzzles(session, now=moment)

    # Rate each daily that just transitioned to finalized.
    if report.finalized_dailies:
        rows = await session.execute(
            select(DailyPuzzle).where(
                DailyPuzzle.id.in_(report.finalized_dailies)
            )
        )
        for daily in rows.scalars():
            results = await finalize_daily_ratings(session, daily, now=moment)
            report.rated_attempts += len(results)
            daily.status = DailyPuzzleStatus.finalized

    return report


__all__ = ["JobReport", "run_due_jobs"]
