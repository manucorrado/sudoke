from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.jobs.tick import run_due_jobs
from src.models import (
    AttemptStatus,
    DailyPuzzle,
    Puzzle,
    PuzzleStatus,
    RankedAttempt,
    User,
    UserRole,
)
from src.models.puzzles import DailyPuzzleStatus, PuzzleDifficulty
from src.sudoku.engine import parse_grid, serialize_grid, solve

EASY = (
    "530070000"
    "600195000"
    "098000060"
    "800060003"
    "400803001"
    "700020006"
    "060000280"
    "000419005"
    "000080079"
)
EASY_SOL = serialize_grid(solve(parse_grid(EASY)) or [])


async def _make_puzzle(session: AsyncSession) -> Puzzle:
    puzzle = Puzzle(
        givens=EASY,
        solution=EASY_SOL,
        difficulty=PuzzleDifficulty.medium,
        status=PuzzleStatus.approved,
        estimated_min_seconds=240,
        estimated_max_seconds=600,
        clue_count=30,
        source="manual",
        license="CC0",
    )
    session.add(puzzle)
    await session.flush()
    return puzzle


@pytest.mark.asyncio
async def test_worker_activates_due_puzzles(db_session: AsyncSession) -> None:
    puzzle = await _make_puzzle(db_session)
    now = datetime.now(timezone.utc)
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today(),
        activate_at=now - timedelta(minutes=1),
        finalize_at=now + timedelta(hours=12),
        status=DailyPuzzleStatus.scheduled,
    )
    db_session.add(daily)
    await db_session.commit()

    report = await run_due_jobs(db_session)
    await db_session.commit()
    await db_session.refresh(daily)

    assert daily.id in report.activated
    assert daily.status == DailyPuzzleStatus.active


@pytest.mark.asyncio
async def test_worker_finalizes_and_rates(db_session: AsyncSession) -> None:
    puzzle = await _make_puzzle(db_session)
    moment = datetime.now(timezone.utc)
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today(),
        activate_at=moment - timedelta(days=1, hours=1),
        finalize_at=moment - timedelta(minutes=1),
        status=DailyPuzzleStatus.active,
    )
    db_session.add(daily)
    await db_session.flush()

    for i in range(11):
        user = User(
            auth_provider_id=f"runner-{i}",
            username=f"runner{i}",
            role=UserRole.player,
        )
        db_session.add(user)
        await db_session.flush()
        attempt = RankedAttempt(
            user_id=user.id,
            daily_puzzle_id=daily.id,
            status=AttemptStatus.provisional_ranked,
            started_at=moment - timedelta(minutes=20),
            submitted_at=moment - timedelta(minutes=2, seconds=i),
            mistakes=0,
            official_duration_ms=300_000 + i * 1_000,
            submitted_grid=EASY_SOL,
        )
        db_session.add(attempt)
    await db_session.commit()

    report = await run_due_jobs(db_session)
    await db_session.commit()

    await db_session.refresh(daily)
    assert daily.id in report.finalized_dailies
    assert report.rated_attempts == 11
    assert daily.status == DailyPuzzleStatus.finalized


@pytest.mark.asyncio
async def test_worker_times_out_in_progress_attempts(
    db_session: AsyncSession,
) -> None:
    puzzle = await _make_puzzle(db_session)
    moment = datetime.now(timezone.utc)
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today(),
        activate_at=moment - timedelta(days=1, hours=1),
        finalize_at=moment - timedelta(minutes=1),
        status=DailyPuzzleStatus.active,
    )
    db_session.add(daily)
    user = User(
        auth_provider_id="afk-1", username="afk", role=UserRole.player
    )
    db_session.add(user)
    await db_session.flush()
    attempt = RankedAttempt(
        user_id=user.id,
        daily_puzzle_id=daily.id,
        status=AttemptStatus.in_progress,
        started_at=moment - timedelta(minutes=30),
    )
    db_session.add(attempt)
    await db_session.commit()

    report = await run_due_jobs(db_session)
    await db_session.commit()

    await db_session.refresh(attempt)
    assert attempt.id in report.timed_out_attempts
    assert attempt.status == AttemptStatus.timed_out
