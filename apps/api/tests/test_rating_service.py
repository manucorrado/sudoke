from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
from src.services.rating import (
    NORMAL_CAP,
    PROVISIONAL_CAP,
    PROVISIONAL_THRESHOLD,
    RATING_FLOOR,
    STARTING_RATING,
    apply_rating_change,
    compute_delta,
    finalize_daily_ratings,
    get_or_create_rating,
    project_for_attempt,
    tier_for_rating,
)
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


async def _make_active_daily(
    session: AsyncSession,
    *,
    difficulty: PuzzleDifficulty = PuzzleDifficulty.medium,
    closed: bool = False,
) -> DailyPuzzle:
    puzzle = Puzzle(
        givens=EASY,
        solution=EASY_SOL,
        difficulty=difficulty,
        status=PuzzleStatus.approved,
        estimated_min_seconds=240,
        estimated_max_seconds=600,
        clue_count=30,
        source="manual",
        license="CC0",
    )
    session.add(puzzle)
    await session.flush()
    now = datetime.now(timezone.utc)
    if closed:
        activate_at = now - timedelta(days=1, hours=1)
        finalize_at = now - timedelta(minutes=1)
        status = DailyPuzzleStatus.finalizing
    else:
        activate_at = now - timedelta(hours=1)
        finalize_at = now + timedelta(hours=12)
        status = DailyPuzzleStatus.active
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today(),
        activate_at=activate_at,
        finalize_at=finalize_at,
        status=status,
    )
    session.add(daily)
    await session.commit()
    await session.refresh(daily, ["puzzle"])
    return daily


def _make_user(idx: int) -> User:
    return User(
        auth_provider_id=f"user-{idx}",
        username=f"user{idx}",
        display_name=f"User {idx}",
        role=UserRole.player,
    )


async def _seed_cohort(
    session: AsyncSession,
    daily: DailyPuzzle,
    *,
    n: int,
    base_duration_ms: int = 300_000,
    starting_rating: int | None = None,
) -> list[tuple[User, RankedAttempt]]:
    """Insert n users + finalized-eligible (provisional_ranked) attempts.

    Attempt durations form an ascending sequence (user 0 is fastest).
    """

    moment = datetime.now(timezone.utc)
    rows: list[tuple[User, RankedAttempt]] = []
    for i in range(n):
        user = _make_user(i)
        session.add(user)
        await session.flush()
        if starting_rating is not None:
            rating = await get_or_create_rating(session, user.id)
            rating.rating = starting_rating
        attempt = RankedAttempt(
            user_id=user.id,
            daily_puzzle_id=daily.id,
            status=AttemptStatus.provisional_ranked,
            started_at=moment - timedelta(minutes=15),
            submitted_at=moment - timedelta(seconds=i),
            mistakes=0,
            official_duration_ms=base_duration_ms + i * 5_000,
            submitted_grid=EASY_SOL,
        )
        session.add(attempt)
        await session.flush()
        rows.append((user, attempt))
    await session.commit()
    return rows


# ---------------------------------------------------------------------------
# Pure-function tests
# ---------------------------------------------------------------------------


def test_compute_delta_caps_provisional() -> None:
    delta = compute_delta(
        current_rating=1000,
        percentile=100.0,
        difficulty=PuzzleDifficulty.hard,
        cohort_size=200,
        is_provisional=True,
    )
    assert delta == PROVISIONAL_CAP


def test_compute_delta_caps_normal() -> None:
    delta = compute_delta(
        current_rating=1000,
        percentile=100.0,
        difficulty=PuzzleDifficulty.hard,
        cohort_size=200,
        is_provisional=False,
    )
    assert delta == NORMAL_CAP


def test_compute_delta_small_cohort_no_movement() -> None:
    delta = compute_delta(
        current_rating=1000,
        percentile=100.0,
        difficulty=PuzzleDifficulty.medium,
        cohort_size=5,
        is_provisional=False,
    )
    assert delta == 0


def test_compute_delta_difficulty_multiplier() -> None:
    easy = compute_delta(
        current_rating=1000,
        percentile=100.0,
        difficulty=PuzzleDifficulty.easy,
        cohort_size=200,
        is_provisional=False,
    )
    hard = compute_delta(
        current_rating=1000,
        percentile=100.0,
        difficulty=PuzzleDifficulty.hard,
        cohort_size=200,
        is_provisional=False,
    )
    assert easy < hard


def test_compute_delta_50th_percentile_no_change() -> None:
    delta = compute_delta(
        current_rating=1000,
        percentile=50.0,
        difficulty=PuzzleDifficulty.medium,
        cohort_size=200,
        is_provisional=False,
    )
    assert delta == 0


def test_apply_rating_change_floor() -> None:
    assert apply_rating_change(120, -50) == 100
    assert apply_rating_change(100, -1000) == RATING_FLOOR
    assert apply_rating_change(500, 50) == 550


def test_tier_for_rating_boundaries() -> None:
    assert tier_for_rating(100) == "bronze"
    assert tier_for_rating(799) == "bronze"
    assert tier_for_rating(800) == "silver"
    assert tier_for_rating(999) == "silver"
    assert tier_for_rating(1000) == "gold"
    assert tier_for_rating(1199) == "gold"
    assert tier_for_rating(1200) == "platinum"
    assert tier_for_rating(1499) == "platinum"
    assert tier_for_rating(1500) == "diamond"
    assert tier_for_rating(1799) == "diamond"
    assert tier_for_rating(1800) == "master"
    assert tier_for_rating(9999) == "master"


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_project_for_attempt_writes_history(db_session: AsyncSession) -> None:
    daily = await _make_active_daily(db_session)
    [(_user, attempt)] = await _seed_cohort(db_session, daily, n=1)

    projection = await project_for_attempt(
        db_session,
        attempt=attempt,
        puzzle_difficulty=PuzzleDifficulty.medium,
    )
    await db_session.commit()

    assert projection is not None
    assert projection.old_rating == STARTING_RATING
    assert projection.calculation_version == "v1"
    # Cohort of one — percentile is set to 50 (no change).
    assert projection.new_rating == STARTING_RATING
    assert projection.is_provisional is True
    assert attempt.calculation_version == "v1"


@pytest.mark.asyncio
async def test_project_for_attempt_is_idempotent(db_session: AsyncSession) -> None:
    """Resubmits should not duplicate `projected` history rows."""

    daily = await _make_active_daily(db_session)
    [(user, attempt)] = await _seed_cohort(db_session, daily, n=1)

    await project_for_attempt(
        db_session, attempt=attempt, puzzle_difficulty=PuzzleDifficulty.medium
    )
    await project_for_attempt(
        db_session, attempt=attempt, puzzle_difficulty=PuzzleDifficulty.medium
    )
    await db_session.commit()

    from sqlalchemy import select

    from src.models import RatingHistory

    rows = (
        await db_session.execute(
            select(RatingHistory).where(RatingHistory.user_id == user.id)
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].kind == "projected"


@pytest.mark.asyncio
async def test_finalize_daily_ratings_assigns_ranks_and_deltas(
    db_session: AsyncSession,
) -> None:
    daily = await _make_active_daily(db_session, closed=True)
    await _seed_cohort(db_session, daily, n=12)  # >= 10 -> dampened

    finalized = await finalize_daily_ratings(db_session, daily)
    await db_session.commit()

    assert len(finalized) == 12
    # User 0 was fastest -> should be rank 1, positive delta.
    fastest = finalized[0]
    assert fastest.rank == 1
    assert fastest.delta > 0
    # User 11 was slowest -> negative delta and rating reduced.
    slowest = finalized[-1]
    assert slowest.rank == 12
    assert slowest.delta < 0


@pytest.mark.asyncio
async def test_finalize_is_idempotent(db_session: AsyncSession) -> None:
    daily = await _make_active_daily(db_session, closed=True)
    cohort = await _seed_cohort(db_session, daily, n=12)

    first = await finalize_daily_ratings(db_session, daily)
    await db_session.commit()
    second = await finalize_daily_ratings(db_session, daily)
    await db_session.commit()

    assert len(first) == 12
    assert len(second) == 0  # nothing left to finalize

    fastest_user_id = cohort[0][0].id
    rating = await get_or_create_rating(db_session, fastest_user_id)
    assert rating.provisional_completions == 1  # NOT incremented twice


@pytest.mark.asyncio
async def test_finalize_marks_attempts_finalized(db_session: AsyncSession) -> None:
    daily = await _make_active_daily(db_session, closed=True)
    cohort = await _seed_cohort(db_session, daily, n=11)

    await finalize_daily_ratings(db_session, daily)
    await db_session.commit()

    for _, attempt in cohort:
        await db_session.refresh(attempt)
        assert attempt.status == AttemptStatus.finalized
        assert attempt.finalized_at is not None


@pytest.mark.asyncio
async def test_provisional_period_uses_larger_cap(db_session: AsyncSession) -> None:
    """A provisional player should move farther than a settled one for the
    same percentile in the same cohort."""

    daily = await _make_active_daily(db_session, closed=True)
    cohort = await _seed_cohort(db_session, daily, n=60)  # >= 50 = full multiplier

    # Make user 0 a non-provisional player to compare with user 1 (provisional).
    rating0 = await get_or_create_rating(db_session, cohort[0][0].id)
    rating0.provisional_completions = PROVISIONAL_THRESHOLD
    await db_session.commit()

    finalized = await finalize_daily_ratings(db_session, daily)
    await db_session.commit()

    by_user = {f.user_id: f for f in finalized}
    settled = by_user[cohort[0][0].id]
    provisional = by_user[cohort[1][0].id]
    # Both finished near the top; the provisional player's delta should be
    # larger in magnitude.
    assert abs(provisional.delta) >= abs(settled.delta)
