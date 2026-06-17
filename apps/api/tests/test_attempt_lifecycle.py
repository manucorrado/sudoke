from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AttemptStatus, DailyPuzzle, Puzzle, PuzzleStatus, User
from src.models.puzzles import DailyPuzzleStatus, PuzzleDifficulty
from src.services.attempts import (
    AttemptError,
    abandon_attempt,
    preview_attempt,
    start_attempt,
    submit_attempt,
)
from src.schemas.common import SubmitAttemptRequest
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


async def _setup_active_daily(session: AsyncSession) -> tuple[DailyPuzzle, Puzzle]:
    puzzle = Puzzle(
        givens=EASY,
        solution=EASY_SOL,
        difficulty=PuzzleDifficulty.medium,
        status=PuzzleStatus.approved,
        estimated_min_seconds=360,
        estimated_max_seconds=720,
        clue_count=30,
        source="manual",
        license="CC0",
    )
    session.add(puzzle)
    await session.flush()
    now = datetime.now(timezone.utc)
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today(),
        activate_at=now - timedelta(minutes=5),
        finalize_at=now + timedelta(hours=12),
        status=DailyPuzzleStatus.active,
    )
    session.add(daily)
    await session.commit()
    await session.refresh(daily, ["puzzle"])
    return daily, puzzle


@pytest.mark.asyncio
async def test_preview_does_not_consume_attempt(
    db_session: AsyncSession, player_user: User
) -> None:
    daily, _puzzle = await _setup_active_daily(db_session)
    attempt = await preview_attempt(
        db_session, daily, user=player_user, guest=None
    )
    await db_session.commit()
    assert attempt.status == AttemptStatus.previewing
    assert attempt.started_at is None
    assert attempt.previewed_at is not None


@pytest.mark.asyncio
async def test_start_then_submit_full_lifecycle(
    db_session: AsyncSession, player_user: User
) -> None:
    daily, puzzle = await _setup_active_daily(db_session)
    await preview_attempt(db_session, daily, user=player_user, guest=None)
    await db_session.commit()

    attempt = await start_attempt(db_session, daily, user=player_user, guest=None)
    await db_session.commit()
    assert attempt.status == AttemptStatus.in_progress
    assert attempt.started_at is not None

    # Slow solve (>= threshold) so the attempt validates.
    submit_ts = attempt.started_at + timedelta(minutes=10)
    result = await submit_attempt(
        db_session,
        attempt,
        daily,
        puzzle,
        SubmitAttemptRequest(submitted_grid=EASY_SOL, mistakes=1),
        now=submit_ts,
    )
    await db_session.commit()
    assert result.status == AttemptStatus.provisional_ranked
    assert result.mistakes == 1
    assert result.official_duration_ms is not None and result.official_duration_ms >= 600_000


@pytest.mark.asyncio
async def test_submit_with_wrong_grid_fails(
    db_session: AsyncSession, player_user: User
) -> None:
    daily, puzzle = await _setup_active_daily(db_session)
    attempt = await start_attempt(db_session, daily, user=player_user, guest=None)
    await db_session.commit()

    bad = list(parse_grid(EASY_SOL))
    bad[0] = (bad[0] % 9) + 1
    bad_str = serialize_grid(bad)
    with pytest.raises(AttemptError):
        await submit_attempt(
            db_session,
            attempt,
            daily,
            puzzle,
            SubmitAttemptRequest(submitted_grid=bad_str, mistakes=0),
        )


@pytest.mark.asyncio
async def test_fast_solve_marked_under_review(
    db_session: AsyncSession, player_user: User
) -> None:
    daily, puzzle = await _setup_active_daily(db_session)
    attempt = await start_attempt(db_session, daily, user=player_user, guest=None)
    await db_session.commit()

    # Submit 5 seconds after start — far below medium threshold (90s).
    submit_ts = attempt.started_at + timedelta(seconds=5) if attempt.started_at else datetime.now(timezone.utc)
    result = await submit_attempt(
        db_session,
        attempt,
        daily,
        puzzle,
        SubmitAttemptRequest(submitted_grid=EASY_SOL, mistakes=0),
        now=submit_ts,
    )
    await db_session.commit()
    assert result.status == AttemptStatus.under_review
    assert result.under_review_reason == "fast_solve_threshold"


@pytest.mark.asyncio
async def test_start_consumes_attempt(
    db_session: AsyncSession, player_user: User
) -> None:
    daily, _puzzle = await _setup_active_daily(db_session)
    await start_attempt(db_session, daily, user=player_user, guest=None)
    await db_session.commit()
    with pytest.raises(AttemptError):
        await start_attempt(db_session, daily, user=player_user, guest=None)


@pytest.mark.asyncio
async def test_abandon_marks_terminal(
    db_session: AsyncSession, player_user: User
) -> None:
    daily, _puzzle = await _setup_active_daily(db_session)
    attempt = await start_attempt(db_session, daily, user=player_user, guest=None)
    await db_session.commit()
    abandoned = await abandon_attempt(db_session, attempt)
    await db_session.commit()
    assert abandoned.status == AttemptStatus.abandoned
    assert abandoned.abandoned_at is not None
