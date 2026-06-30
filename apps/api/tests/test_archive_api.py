"""Archive listing + ghost rank (Epic 7)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
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
from src.middleware.auth import AuthenticatedUser
from src.models.puzzles import DailyPuzzleStatus, PuzzleDifficulty
from src.services.rating import finalize_daily_ratings
from src.sudoku.engine import parse_grid, serialize_grid, solve
from tests.conftest import auth_headers, login_as

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


async def _seed(
    db_session: AsyncSession,
    *,
    days_ago: int,
    n_results: int = 0,
    finalized: bool = True,
) -> tuple[DailyPuzzle, list[User]]:
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
    db_session.add(puzzle)
    await db_session.flush()
    now = datetime.now(timezone.utc) - timedelta(days=days_ago)
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today() - timedelta(days=days_ago),
        activate_at=now,
        finalize_at=now + timedelta(hours=23),
        status=DailyPuzzleStatus.active,
    )
    db_session.add(daily)
    await db_session.flush()
    users: list[User] = []
    for i in range(n_results):
        user = User(
            auth_provider_id=f"archive-user-{days_ago}-{i}",
            username=f"u{days_ago}{i}",
            role=UserRole.player,
        )
        db_session.add(user)
        await db_session.flush()
        attempt = RankedAttempt(
            user_id=user.id,
            daily_puzzle_id=daily.id,
            status=AttemptStatus.provisional_ranked,
            started_at=now,
            submitted_at=now + timedelta(minutes=10 + i),
            mistakes=0,
            official_duration_ms=300_000 + i * 5_000,
            submitted_grid=EASY_SOL,
        )
        db_session.add(attempt)
        users.append(user)
    await db_session.commit()
    if finalized:
        daily.status = DailyPuzzleStatus.finalizing
        await finalize_daily_ratings(db_session, daily)
        daily.status = DailyPuzzleStatus.finalized
        await db_session.commit()
    return daily, users


@pytest.mark.asyncio
async def test_archive_list_returns_closed_puzzles(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, days_ago=2, n_results=3)
    await _seed(db_session, days_ago=1, n_results=2)

    res = await client.get("/api/v1/archive")
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["entries"]) == 2
    # Newest first
    assert body["entries"][0]["scheduled_for"] > body["entries"][1]["scheduled_for"]


@pytest.mark.asyncio
async def test_archive_detail_exposes_solution(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    daily, _ = await _seed(db_session, days_ago=1, n_results=0)
    res = await client.get(f"/api/v1/archive/{daily.id}")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["givens"] == EASY
    assert body["solution"] == EASY_SOL


@pytest.mark.asyncio
async def test_archive_detail_blocks_open_daily(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """An active (non-finalized) daily must NOT be exposed via archive."""

    puzzle = Puzzle(
        givens=EASY,
        solution=EASY_SOL,
        difficulty=PuzzleDifficulty.easy,
        status=PuzzleStatus.approved,
        estimated_min_seconds=240,
        estimated_max_seconds=600,
        clue_count=30,
        source="m",
        license="CC0",
    )
    db_session.add(puzzle)
    await db_session.flush()
    now = datetime.now(timezone.utc)
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today(),
        activate_at=now - timedelta(hours=1),
        finalize_at=now + timedelta(hours=20),
        status=DailyPuzzleStatus.active,
    )
    db_session.add(daily)
    await db_session.commit()

    res = await client.get(f"/api/v1/archive/{daily.id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_ghost_rank_against_finalized_cohort(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    daily, _ = await _seed(db_session, days_ago=2, n_results=5)
    # Cohort durations: 300000, 305000, 310000, 315000, 320000 (all 0 mistakes)
    # A 307s play should place 3rd.
    res = await client.post(
        f"/api/v1/archive/{daily.id}/ghost-rank",
        json={"duration_ms": 307_000, "mistakes": 0},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["cohort_size"] == 5
    assert body["ghost_rank"] == 3
    assert body["percentile"] is not None


@pytest.mark.asyncio
async def test_upcoming_lists_only_future(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Insert one future-scheduled puzzle.
    puzzle = Puzzle(
        givens=EASY,
        solution=EASY_SOL,
        difficulty=PuzzleDifficulty.hard,
        status=PuzzleStatus.approved,
        estimated_min_seconds=600,
        estimated_max_seconds=1200,
        clue_count=22,
        source="m",
        license="CC0",
    )
    db_session.add(puzzle)
    await db_session.flush()
    now = datetime.now(timezone.utc)
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today() + timedelta(days=3),
        activate_at=now + timedelta(days=3),
        finalize_at=now + timedelta(days=4),
        status=DailyPuzzleStatus.scheduled,
    )
    db_session.add(daily)
    await db_session.commit()

    res = await client.get("/api/v1/archive/upcoming")
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["entries"]) == 1
    entry = body["entries"][0]
    assert entry["difficulty"] == "hard"
    # No givens, no solution
    assert "givens" not in entry


@pytest.mark.asyncio
async def test_archive_my_result_returns_original_result(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A user who played the daily sees their finalized result in archive."""

    daily, users = await _seed(db_session, days_ago=3, n_results=3)
    me = users[0]  # fastest cohort time -> rank 1
    login_as(client, AuthenticatedUser(user_id=me.auth_provider_id, email=me.email))

    res = await client.get(
        f"/api/v1/archive/{daily.id}/my-result", headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["played"] is True
    assert body["daily_puzzle_id"] == str(daily.id)
    assert body["result"]["rank"] == 1
    assert body["result"]["is_final"] is True
    assert body["result"]["cohort_size"] == 3


@pytest.mark.asyncio
async def test_archive_my_result_not_played_returns_null(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    """A user who never attempted the daily gets played=False (not a 404)."""

    daily, _ = await _seed(db_session, days_ago=2, n_results=2)
    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id, email=player_user.email
        ),
    )

    res = await client.get(
        f"/api/v1/archive/{daily.id}/my-result", headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["played"] is False
    assert body["result"] is None


@pytest.mark.asyncio
async def test_archive_my_result_open_daily_404(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    """An open (non-closed) daily is not an archive entry -> 404."""

    puzzle = Puzzle(
        givens=EASY,
        solution=EASY_SOL,
        difficulty=PuzzleDifficulty.easy,
        status=PuzzleStatus.approved,
        estimated_min_seconds=240,
        estimated_max_seconds=600,
        clue_count=30,
        source="m",
        license="CC0",
    )
    db_session.add(puzzle)
    await db_session.flush()
    now = datetime.now(timezone.utc)
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today(),
        activate_at=now - timedelta(hours=1),
        finalize_at=now + timedelta(hours=20),
        status=DailyPuzzleStatus.active,
    )
    db_session.add(daily)
    await db_session.commit()

    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id, email=player_user.email
        ),
    )
    res = await client.get(
        f"/api/v1/archive/{daily.id}/my-result", headers=auth_headers()
    )
    assert res.status_code == 404
