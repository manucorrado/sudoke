"""Archive + ghost rank queries (PRD §12, Epic 7).

The archive lists daily puzzles whose window has closed (finalized or
past `finalize_at`). The Play tab uses this to power non-ranked replay.

Ghost rank takes a (duration, mistakes) tuple from a practice play and
returns the rank/percentile the user *would* have achieved had they
played within the daily window. It's strictly read-only and clearly
marked unofficial on the client.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import DailyPuzzle, DailyPuzzleStatus, DailyResult, Puzzle


@dataclass(frozen=True)
class ArchiveEntry:
    daily_puzzle_id: uuid.UUID
    puzzle_id: uuid.UUID
    scheduled_for: date
    difficulty: str
    estimated_min_seconds: int
    estimated_max_seconds: int
    is_final: bool


@dataclass(frozen=True)
class ArchiveDetail:
    daily_puzzle_id: uuid.UUID
    puzzle_id: uuid.UUID
    scheduled_for: date
    difficulty: str
    estimated_min_seconds: int
    estimated_max_seconds: int
    givens: str
    solution: str
    is_final: bool


@dataclass(frozen=True)
class UpcomingEntry:
    scheduled_for: date
    difficulty: str


@dataclass(frozen=True)
class GhostRank:
    daily_puzzle_id: uuid.UUID
    duration_ms: int
    mistakes: int
    ghost_rank: int | None
    cohort_size: int
    percentile: float | None


def _is_closed(
    daily: DailyPuzzle, *, now: datetime
) -> bool:
    return (
        daily.status == DailyPuzzleStatus.finalized
        or daily.finalize_at <= now
    )


async def list_archive(
    session: AsyncSession,
    *,
    limit: int = 30,
    offset: int = 0,
    now: datetime | None = None,
) -> list[ArchiveEntry]:
    """Return closed daily puzzles, newest first."""

    moment = now or datetime.now(timezone.utc)
    stmt = (
        select(DailyPuzzle, Puzzle)
        .join(Puzzle, DailyPuzzle.puzzle_id == Puzzle.id)
        .where(DailyPuzzle.finalize_at <= moment)
        .order_by(DailyPuzzle.scheduled_for.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).all()
    return [
        ArchiveEntry(
            daily_puzzle_id=daily.id,
            puzzle_id=puzzle.id,
            scheduled_for=daily.scheduled_for,
            difficulty=puzzle.difficulty.value,
            estimated_min_seconds=puzzle.estimated_min_seconds,
            estimated_max_seconds=puzzle.estimated_max_seconds,
            is_final=_is_closed(daily, now=moment),
        )
        for daily, puzzle in rows
    ]


async def get_archive_detail(
    session: AsyncSession,
    daily_puzzle_id: uuid.UUID,
    *,
    now: datetime | None = None,
) -> ArchiveDetail | None:
    moment = now or datetime.now(timezone.utc)
    stmt = (
        select(DailyPuzzle, Puzzle)
        .join(Puzzle, DailyPuzzle.puzzle_id == Puzzle.id)
        .where(DailyPuzzle.id == daily_puzzle_id)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    daily, puzzle = row
    if not _is_closed(daily, now=moment):
        return None
    return ArchiveDetail(
        daily_puzzle_id=daily.id,
        puzzle_id=puzzle.id,
        scheduled_for=daily.scheduled_for,
        difficulty=puzzle.difficulty.value,
        estimated_min_seconds=puzzle.estimated_min_seconds,
        estimated_max_seconds=puzzle.estimated_max_seconds,
        givens=puzzle.givens,
        solution=puzzle.solution,
        is_final=True,
    )


async def list_upcoming(
    session: AsyncSession,
    *,
    limit: int = 14,
    now: datetime | None = None,
) -> list[UpcomingEntry]:
    """Return scheduled puzzles whose activation is still in the future.

    Only the difficulty + date is exposed — never the puzzle content
    (§12 — no puzzle leak).
    """

    moment = now or datetime.now(timezone.utc)
    stmt = (
        select(DailyPuzzle, Puzzle)
        .join(Puzzle, DailyPuzzle.puzzle_id == Puzzle.id)
        .where(DailyPuzzle.activate_at > moment)
        .order_by(DailyPuzzle.scheduled_for.asc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        UpcomingEntry(
            scheduled_for=daily.scheduled_for,
            difficulty=puzzle.difficulty.value,
        )
        for daily, puzzle in rows
    ]


async def compute_ghost_rank(
    session: AsyncSession,
    daily_puzzle_id: uuid.UUID,
    *,
    duration_ms: int,
    mistakes: int,
) -> GhostRank | None:
    """Compute the rank the (duration, mistakes) would have earned.

    Uses finalized DailyResult rows for stability. Returns None when the
    daily is not yet finalized.
    """

    stmt = (
        select(DailyResult)
        .where(DailyResult.daily_puzzle_id == daily_puzzle_id)
        .order_by(
            DailyResult.mistakes.asc(),
            DailyResult.official_duration_ms.asc(),
        )
    )
    rows = list((await session.execute(stmt)).scalars())
    cohort = len(rows)
    if cohort == 0:
        return GhostRank(
            daily_puzzle_id=daily_puzzle_id,
            duration_ms=duration_ms,
            mistakes=mistakes,
            ghost_rank=None,
            cohort_size=0,
            percentile=None,
        )

    rank = 1
    for r in rows:
        if (mistakes, duration_ms) <= (r.mistakes, r.official_duration_ms):
            break
        rank += 1
    rank = min(rank, cohort + 1)

    # Percentile: fraction of cohort the player beats (lower is better).
    percentile = (cohort - rank + 1) / cohort * 100 if cohort else None
    return GhostRank(
        daily_puzzle_id=daily_puzzle_id,
        duration_ms=duration_ms,
        mistakes=mistakes,
        ghost_rank=rank,
        cohort_size=cohort,
        percentile=round(percentile, 2) if percentile is not None else None,
    )


__all__ = [
    "ArchiveDetail",
    "ArchiveEntry",
    "GhostRank",
    "UpcomingEntry",
    "compute_ghost_rank",
    "get_archive_detail",
    "list_archive",
    "list_upcoming",
]
