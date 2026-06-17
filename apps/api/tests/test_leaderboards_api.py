from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.auth import AuthenticatedUser
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


async def _seed_daily_with_cohort(
    session: AsyncSession, n: int, *, finalized: bool = False
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
    session.add(puzzle)
    await session.flush()
    now = datetime.now(timezone.utc)
    daily = DailyPuzzle(
        puzzle_id=puzzle.id,
        scheduled_for=date.today(),
        activate_at=now - timedelta(hours=2),
        finalize_at=(
            now - timedelta(minutes=5)
            if finalized
            else now + timedelta(hours=12)
        ),
        status=(
            DailyPuzzleStatus.finalizing if finalized else DailyPuzzleStatus.active
        ),
    )
    session.add(daily)
    await session.flush()
    users: list[User] = []
    for i in range(n):
        user = User(
            auth_provider_id=f"player-{i}",
            username=f"player{i}",
            display_name=f"Player {i}",
            role=UserRole.player,
        )
        session.add(user)
        await session.flush()
        attempt = RankedAttempt(
            user_id=user.id,
            daily_puzzle_id=daily.id,
            status=AttemptStatus.provisional_ranked,
            started_at=now - timedelta(minutes=15),
            submitted_at=now - timedelta(seconds=i),
            mistakes=0,
            official_duration_ms=300_000 + i * 5_000,
            submitted_grid=EASY_SOL,
        )
        session.add(attempt)
        users.append(user)
    await session.commit()
    if finalized:
        await finalize_daily_ratings(session, daily)
        daily.status = DailyPuzzleStatus.finalized
        await session.commit()
    await session.refresh(daily, ["puzzle"])
    return daily, users


@pytest.mark.asyncio
async def test_leaderboard_global_live(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    daily, users = await _seed_daily_with_cohort(db_session, n=12)
    login_as(
        client,
        AuthenticatedUser(
            user_id=users[0].auth_provider_id, email=users[0].email
        ),
    )

    res = await client.get(
        f"/api/v1/daily/{daily.id}/leaderboard?view=global&limit=10",
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["view"] == "global"
    assert body["cohort_size"] == 12
    assert body["is_final"] is False
    assert len(body["rows"]) == 10
    assert body["rows"][0]["rank"] == 1
    assert body["rows"][0]["is_me"] is True


@pytest.mark.asyncio
async def test_leaderboard_nearby_centers_on_me(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    daily, users = await _seed_daily_with_cohort(db_session, n=20)
    me = users[10]  # roughly middle of pack
    login_as(
        client,
        AuthenticatedUser(user_id=me.auth_provider_id, email=me.email),
    )

    res = await client.get(
        f"/api/v1/daily/{daily.id}/leaderboard?view=nearby&limit=5",
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    ranks = [row["rank"] for row in body["rows"]]
    assert me.id.hex in [row["user_id"].replace("-", "") for row in body["rows"]]
    assert len(ranks) == 5
    # The window should contain my rank (11).
    assert 11 in ranks


@pytest.mark.asyncio
async def test_my_result_live(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    daily, users = await _seed_daily_with_cohort(db_session, n=15)
    me = users[3]
    login_as(
        client,
        AuthenticatedUser(user_id=me.auth_provider_id, email=me.email),
    )
    res = await client.get(
        f"/api/v1/daily/{daily.id}/my-result", headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["rank"] == 4  # user index 3 -> rank 4
    assert body["cohort_size"] == 15
    assert body["is_final"] is False
    assert body["status"] == "provisional_ranked"


@pytest.mark.asyncio
async def test_my_result_after_finalization(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    daily, users = await _seed_daily_with_cohort(db_session, n=12, finalized=True)
    me = users[0]
    login_as(
        client,
        AuthenticatedUser(user_id=me.auth_provider_id, email=me.email),
    )
    res = await client.get(
        f"/api/v1/daily/{daily.id}/my-result", headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["is_final"] is True
    assert body["rank"] == 1
    assert body["rating_after"] > body["rating_before"]


@pytest.mark.asyncio
async def test_me_rating_endpoint(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id, email=player_user.email
        ),
    )
    res = await client.get("/api/v1/me/rating", headers=auth_headers())
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["rating"] == 1000
    assert body["tier"] == "gold"
    assert body["is_provisional"] is True
    assert body["provisional_completions"] == 0


@pytest.mark.asyncio
async def test_me_rating_history_after_finalization(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _daily, users = await _seed_daily_with_cohort(
        db_session, n=12, finalized=True
    )
    me = users[0]
    login_as(
        client,
        AuthenticatedUser(user_id=me.auth_provider_id, email=me.email),
    )
    res = await client.get(
        "/api/v1/me/rating/history?kind=final", headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["entries"]) == 1
    entry = body["entries"][0]
    assert entry["kind"] == "final"
    assert entry["delta"] > 0
    assert entry["cohort_size"] == 12


@pytest.mark.asyncio
async def test_my_result_without_attempt_404(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    daily, _users = await _seed_daily_with_cohort(db_session, n=2)
    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id, email=player_user.email
        ),
    )
    res = await client.get(
        f"/api/v1/daily/{daily.id}/my-result", headers=auth_headers()
    )
    assert res.status_code == 404
