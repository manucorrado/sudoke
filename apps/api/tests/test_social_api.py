"""Friends graph + challenges (Epic 6)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.auth import AuthenticatedUser
from src.models import (
    AttemptStatus,
    ChallengeAcceptance,
    DailyPuzzle,
    GuestSession,
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
    *,
    scheduled_for: date | None = None,
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
        scheduled_for=scheduled_for or date.today(),
        activate_at=now - timedelta(hours=1),
        finalize_at=now + timedelta(hours=20),
        status=DailyPuzzleStatus.active,
    )
    db_session.add(daily)
    await db_session.commit()
    return daily


async def _create_guest(
    client: AsyncClient, db_session: AsyncSession
) -> GuestSession:
    login_as(client, None)
    res = await client.post("/api/v1/guest/sessions", json={"locale": "en-US"})
    assert res.status_code == 201, res.text
    token = res.json()["token"]
    guest = (
        await db_session.execute(
            select(GuestSession).where(GuestSession.token == token)
        )
    ).scalar_one()
    return guest


def _complete_attempt_for_guest(
    daily: DailyPuzzle,
    guest: GuestSession,
    *,
    duration_ms: int = 320_000,
    mistakes: int = 1,
) -> RankedAttempt:
    now = datetime.now(timezone.utc)
    return RankedAttempt(
        guest_session_id=guest.id,
        daily_puzzle_id=daily.id,
        status=AttemptStatus.provisional_ranked,
        started_at=now - timedelta(milliseconds=duration_ms),
        submitted_at=now,
        mistakes=mistakes,
        official_duration_ms=duration_ms,
        submitted_grid=EASY_SOL,
    )


def _complete_attempt_for_user(
    daily: DailyPuzzle,
    user: User,
    *,
    duration_ms: int = 300_000,
    mistakes: int = 0,
) -> RankedAttempt:
    now = datetime.now(timezone.utc)
    return RankedAttempt(
        user_id=user.id,
        daily_puzzle_id=daily.id,
        status=AttemptStatus.provisional_ranked,
        started_at=now - timedelta(milliseconds=duration_ms),
        submitted_at=now,
        mistakes=mistakes,
        official_duration_ms=duration_ms,
        submitted_grid=EASY_SOL,
    )


async def _claim_guest(
    client: AsyncClient, user: User, guest: GuestSession
) -> Response:
    login_as(
        client,
        AuthenticatedUser(user_id=user.auth_provider_id, email=user.email),
    )
    return await client.post(
        "/api/v1/me/claim-guest",
        headers={**auth_headers(), "X-Guest-Token": guest.token},
    )


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


@pytest.mark.asyncio
async def test_record_challenge_acceptance_guest_happy_path(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    daily = await _seed_active_daily(db_session)

    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.post(
        "/api/v1/me/challenges", json={}, headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    challenge_id = res.json()["id"]

    guest = await _create_guest(client, db_session)
    attempt = _complete_attempt_for_guest(daily, guest, duration_ms=345_000, mistakes=2)
    db_session.add(attempt)
    await db_session.commit()

    res = await client.post(
        f"/api/v1/challenges/{challenge_id}/results",
        headers={"X-Guest-Token": guest.token},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["challenge_id"] == challenge_id
    assert body["duration_ms"] == 345_000
    assert body["mistakes"] == 2
    assert body["completed_at"] is not None


@pytest.mark.asyncio
async def test_record_challenge_rejects_daily_mismatch(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    challenge_daily = await _seed_active_daily(db_session)
    other_daily = await _seed_active_daily(
        db_session, scheduled_for=challenge_daily.scheduled_for + timedelta(days=1)
    )

    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.post(
        "/api/v1/me/challenges",
        json={"daily_puzzle_id": str(challenge_daily.id)},
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    challenge_id = res.json()["id"]

    guest = await _create_guest(client, db_session)
    db_session.add(_complete_attempt_for_guest(other_daily, guest))
    await db_session.commit()

    res = await client.post(
        f"/api/v1/challenges/{challenge_id}/results",
        headers={"X-Guest-Token": guest.token},
    )
    assert res.status_code == 409, res.text
    assert res.json()["detail"]["code"] == "daily_mismatch"


@pytest.mark.asyncio
async def test_record_challenge_rejects_self(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    daily = await _seed_active_daily(db_session)
    db_session.add(_complete_attempt_for_user(daily, alice))
    await db_session.commit()

    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.post(
        "/api/v1/me/challenges", json={}, headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    challenge_id = res.json()["id"]

    res = await client.post(
        f"/api/v1/challenges/{challenge_id}/results", headers=auth_headers()
    )
    assert res.status_code == 400, res.text
    assert res.json()["detail"]["code"] == "self_challenge"


@pytest.mark.asyncio
async def test_record_challenge_idempotent_update(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    daily = await _seed_active_daily(db_session)

    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.post(
        "/api/v1/me/challenges", json={}, headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    challenge_id = res.json()["id"]

    guest = await _create_guest(client, db_session)
    attempt = _complete_attempt_for_guest(daily, guest, duration_ms=360_000, mistakes=2)
    db_session.add(attempt)
    await db_session.commit()

    res = await client.post(
        f"/api/v1/challenges/{challenge_id}/results",
        headers={"X-Guest-Token": guest.token},
    )
    assert res.status_code == 200, res.text
    first = res.json()

    attempt.official_duration_ms = 330_000
    attempt.mistakes = 1
    await db_session.commit()

    res = await client.post(
        f"/api/v1/challenges/{challenge_id}/results",
        headers={"X-Guest-Token": guest.token},
    )
    assert res.status_code == 200, res.text
    second = res.json()
    assert second["id"] == first["id"]
    assert second["duration_ms"] == 330_000
    assert second["mistakes"] == 1


# ---- Guest claim -------------------------------------------------------


@pytest.mark.asyncio
async def test_claim_guest_attaches_challenge_acceptance(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    bob = await _make_user(db_session, username="bob")
    daily = await _seed_active_daily(db_session)

    login_as(
        client,
        AuthenticatedUser(user_id=alice.auth_provider_id, email=alice.email),
    )
    res = await client.post(
        "/api/v1/me/challenges", json={}, headers=auth_headers()
    )
    assert res.status_code == 200, res.text
    challenge_id = res.json()["id"]

    guest = await _create_guest(client, db_session)
    attempt = _complete_attempt_for_guest(daily, guest)
    db_session.add(attempt)
    await db_session.commit()

    res = await client.post(
        f"/api/v1/challenges/{challenge_id}/results",
        headers={"X-Guest-Token": guest.token},
    )
    assert res.status_code == 200, res.text

    res = await _claim_guest(client, bob, guest)
    assert res.status_code == 200, res.text
    assert res.json()["id"] == str(bob.id)

    acceptance = (
        await db_session.execute(
            select(ChallengeAcceptance).where(
                ChallengeAcceptance.challenge_id == UUID(challenge_id)
            )
        )
    ).scalar_one()
    assert acceptance.recipient_user_id == bob.id
    assert acceptance.recipient_guest_id == guest.id
    await db_session.refresh(guest)
    await db_session.refresh(bob)
    assert guest.claimed_by_user_id == bob.id
    assert guest.claimed_at is not None
    assert bob.claimed_from_guest_id == guest.id


@pytest.mark.asyncio
async def test_claim_guest_attaches_ranked_attempt_without_conflict(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    bob = await _make_user(db_session, username="bob")
    daily = await _seed_active_daily(db_session)
    guest = await _create_guest(client, db_session)
    attempt = _complete_attempt_for_guest(daily, guest)
    db_session.add(attempt)
    await db_session.commit()

    res = await _claim_guest(client, bob, guest)
    assert res.status_code == 200, res.text

    await db_session.refresh(attempt)
    assert attempt.user_id == bob.id
    assert attempt.guest_session_id == guest.id


@pytest.mark.asyncio
async def test_claim_guest_skips_ranked_attempt_when_user_attempt_exists(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    bob = await _make_user(db_session, username="bob")
    daily = await _seed_active_daily(db_session)
    guest = await _create_guest(client, db_session)
    guest_attempt = _complete_attempt_for_guest(daily, guest)
    user_attempt = _complete_attempt_for_user(daily, bob)
    db_session.add_all([guest_attempt, user_attempt])
    await db_session.commit()

    res = await _claim_guest(client, bob, guest)
    assert res.status_code == 200, res.text

    await db_session.refresh(guest_attempt)
    await db_session.refresh(user_attempt)
    assert guest_attempt.user_id is None
    assert guest_attempt.guest_session_id == guest.id
    assert user_attempt.user_id == bob.id


@pytest.mark.asyncio
async def test_claim_guest_is_idempotent_for_same_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    bob = await _make_user(db_session, username="bob")
    daily = await _seed_active_daily(db_session)
    guest = await _create_guest(client, db_session)
    attempt = _complete_attempt_for_guest(daily, guest)
    db_session.add(attempt)
    await db_session.commit()

    first = await _claim_guest(client, bob, guest)
    assert first.status_code == 200, first.text
    second = await _claim_guest(client, bob, guest)
    assert second.status_code == 200, second.text

    await db_session.refresh(attempt)
    await db_session.refresh(guest)
    await db_session.refresh(bob)
    assert attempt.user_id == bob.id
    assert guest.claimed_by_user_id == bob.id
    assert bob.claimed_from_guest_id == guest.id


@pytest.mark.asyncio
async def test_claim_guest_rejects_guest_claimed_by_another_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    alice = await _make_user(db_session, username="alice")
    bob = await _make_user(db_session, username="bob")
    guest = await _create_guest(client, db_session)
    guest.claimed_by_user_id = alice.id
    guest.claimed_at = datetime.now(timezone.utc)
    await db_session.commit()

    res = await _claim_guest(client, bob, guest)
    assert res.status_code == 409, res.text
    assert res.json()["detail"]["code"] == "guest_already_claimed"
