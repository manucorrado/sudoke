"""Friends graph + challenges (Epic 6)."""

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


async def _make_user(
    db_session: AsyncSession, *, username: str
) -> User:
    user = User(
        auth_provider_id=f"u-{username}",
        username=username,
        display_name=username.capitalize(),
        role=UserRole.player,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def _seed_active_daily(
    db_session: AsyncSession,
) -> DailyPuzzle:
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
    return daily


# ---- Friends -----------------------------------------------------------


@pytest.mark.asyncio
async def test_friend_request_lifecycle(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    bob = await _make_user(db_session, username="bob")
    await db_session.commit()

    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.post(
        "/api/v1/me/friends/requests",
        json={"username": "bob"},
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    request_id = body["id"]
    assert body["status"] == "pending"

    # Bob sees the incoming request.
    login_as(
        client,
        AuthenticatedUser(user_id=bob.auth_provider_id, email=bob.email),
    )
    res = await client.get("/api/v1/me/friends/requests", headers=auth_headers())
    body = res.json()
    assert len(body["incoming"]) == 1
    assert body["incoming"][0]["from_username"] == "alice"

    res = await client.post(
        f"/api/v1/me/friends/requests/{request_id}/accept",
        headers=auth_headers(),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "accepted"

    # Both see each other in friends.
    res = await client.get("/api/v1/me/friends", headers=auth_headers())
    assert len(res.json()["friends"]) == 1

    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.get("/api/v1/me/friends", headers=auth_headers())
    assert len(res.json()["friends"]) == 1


@pytest.mark.asyncio
async def test_user_search_and_relationship(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    bob = await _make_user(db_session, username="bob")
    await _make_user(db_session, username="charlie")
    await db_session.commit()

    # Alice sends a request to Bob.
    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    await client.post(
        "/api/v1/me/friends/requests",
        json={"username": "bob"},
        headers=auth_headers(),
    )

    res = await client.get(
        "/api/v1/users/search?q=b", headers=auth_headers()
    )
    body = res.json()
    rels = {r["username"]: r["relationship"] for r in body["results"]}
    assert rels.get("bob") == "request_sent"

    login_as(
        client,
        AuthenticatedUser(user_id=bob.auth_provider_id, email=bob.email),
    )
    res = await client.get(
        "/api/v1/users/search?q=ali", headers=auth_headers()
    )
    rels = {r["username"]: r["relationship"] for r in res.json()["results"]}
    assert rels.get("alice") == "request_received"


@pytest.mark.asyncio
async def test_leaderboard_friends_view_includes_only_friends(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    bob = await _make_user(db_session, username="bob")
    carol = await _make_user(db_session, username="carol")

    daily = await _seed_active_daily(db_session)
    now = datetime.now(timezone.utc)
    for i, u in enumerate([alice, bob, carol]):
        attempt = RankedAttempt(
            user_id=u.id,
            daily_puzzle_id=daily.id,
            status=AttemptStatus.provisional_ranked,
            started_at=now - timedelta(minutes=15),
            submitted_at=now - timedelta(minutes=1, seconds=i),
            mistakes=0,
            official_duration_ms=300_000 + i * 5_000,
            submitted_grid=EASY_SOL,
        )
        db_session.add(attempt)
    await db_session.commit()

    # Alice befriends Bob, ignores Carol.
    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.post(
        "/api/v1/me/friends/requests",
        json={"username": "bob"},
        headers=auth_headers(),
    )
    rid = res.json()["id"]
    login_as(
        client,
        AuthenticatedUser(user_id=bob.auth_provider_id, email=bob.email),
    )
    await client.post(
        f"/api/v1/me/friends/requests/{rid}/accept", headers=auth_headers()
    )

    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.get(
        f"/api/v1/daily/{daily.id}/leaderboard?view=friends&limit=10",
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    usernames = {r["username"] for r in body["rows"]}
    assert usernames == {"alice", "bob"}


# ---- Challenges --------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_resolve_challenge(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    await _seed_active_daily(db_session)

    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.post(
        "/api/v1/me/challenges", json={}, headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    challenge = res.json()
    assert challenge["code"]
    assert challenge["share_url"].endswith(challenge["code"])

    # Public resolution by code (no auth).
    login_as(client, None)
    res = await client.get(
        f"/api/v1/challenges/by-code/{challenge['code']}"
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["challenge"]["id"] == challenge["id"]
    assert body["daily_difficulty"] == "easy"
    assert body["acceptances"] == []
