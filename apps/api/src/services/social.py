"""Friends + challenges service (PRD §16, Epic 6)."""

from __future__ import annotations

import secrets
import string
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    AttemptStatus,
    Challenge,
    ChallengeAcceptance,
    ChallengeStatus,
    DailyPuzzle,
    FriendRequest,
    FriendRequestStatus,
    GuestSession,
    RankedAttempt,
    User,
)

CHALLENGE_CODE_ALPHABET = string.ascii_uppercase + string.digits
CHALLENGE_CODE_LENGTH = 8
CHALLENGE_EXPIRY_HOURS = 48
SUCCESSFUL_CHALLENGE_STATUSES: frozenset[AttemptStatus] = frozenset(
    {
        AttemptStatus.validated,
        AttemptStatus.provisional_ranked,
        AttemptStatus.finalized,
        AttemptStatus.under_review,
    }
)

Relationship = Literal[
    "self", "friends", "request_sent", "request_received", "none"
]


class SocialError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


# ---------------------------------------------------------------------------
# Friends graph
# ---------------------------------------------------------------------------


async def _accepted_friend_user_ids(
    session: AsyncSession, user: User
) -> set[uuid.UUID]:
    stmt = select(FriendRequest).where(
        FriendRequest.status == FriendRequestStatus.accepted
    ).where(
        or_(
            FriendRequest.from_user_id == user.id,
            FriendRequest.to_user_id == user.id,
        )
    )
    rows = list((await session.execute(stmt)).scalars())
    return {
        r.to_user_id if r.from_user_id == user.id else r.from_user_id
        for r in rows
    }


async def get_friend_ids(
    session: AsyncSession, user: User
) -> set[uuid.UUID]:
    return await _accepted_friend_user_ids(session, user)


async def list_friends(
    session: AsyncSession, user: User
) -> list[tuple[User, datetime]]:
    """Returns (other_user, friend_since) for every accepted friend."""

    stmt = (
        select(FriendRequest)
        .where(FriendRequest.status == FriendRequestStatus.accepted)
        .where(
            or_(
                FriendRequest.from_user_id == user.id,
                FriendRequest.to_user_id == user.id,
            )
        )
    )
    rows = list((await session.execute(stmt)).scalars())
    if not rows:
        return []
    other_ids = {
        r.to_user_id if r.from_user_id == user.id else r.from_user_id
        for r in rows
    }
    other_users = await _users_by_ids(session, list(other_ids))
    out: list[tuple[User, datetime]] = []
    for r in rows:
        other_id = (
            r.to_user_id if r.from_user_id == user.id else r.from_user_id
        )
        other = other_users.get(other_id)
        if other is not None:
            out.append((other, r.responded_at or r.updated_at))
    out.sort(
        key=lambda t: (t[0].display_name or t[0].username or "").lower()
    )
    return out


async def _users_by_ids(
    session: AsyncSession, ids: list[uuid.UUID]
) -> dict[uuid.UUID, User]:
    if not ids:
        return {}
    stmt = select(User).where(User.id.in_(ids))
    result = await session.execute(stmt)
    return {u.id: u for u in result.scalars()}


async def _find_request_between(
    session: AsyncSession, a: uuid.UUID, b: uuid.UUID
) -> FriendRequest | None:
    stmt = select(FriendRequest).where(
        or_(
            and_(
                FriendRequest.from_user_id == a, FriendRequest.to_user_id == b
            ),
            and_(
                FriendRequest.from_user_id == b, FriendRequest.to_user_id == a
            ),
        )
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def relationship_with(
    session: AsyncSession, me: User, other: User
) -> Relationship:
    if me.id == other.id:
        return "self"
    req = await _find_request_between(session, me.id, other.id)
    if req is None:
        return "none"
    if req.status == FriendRequestStatus.accepted:
        return "friends"
    if req.status == FriendRequestStatus.pending:
        if req.from_user_id == me.id:
            return "request_sent"
        return "request_received"
    return "none"


async def search_users(
    session: AsyncSession,
    me: User,
    query: str,
    *,
    limit: int = 10,
) -> list[tuple[User, Relationship]]:
    q = (query or "").strip()
    if not q:
        return []
    pattern = f"%{q.lower()}%"
    stmt = (
        select(User)
        .where(User.is_guest.is_(False))
        .where(User.id != me.id)
        .where(
            or_(
                User.username.ilike(pattern),
                User.display_name.ilike(pattern),
            )
        )
        .limit(limit)
    )
    users = list((await session.execute(stmt)).scalars())
    rels = [(u, await relationship_with(session, me, u)) for u in users]
    return rels


async def send_friend_request(
    session: AsyncSession, *, me: User, target_username: str
) -> FriendRequest:
    if not target_username:
        raise SocialError("username_required", "Username is required")
    stmt = select(User).where(User.username == target_username)
    target = (await session.execute(stmt)).scalar_one_or_none()
    if target is None:
        raise SocialError("user_not_found", "User not found", http_status=404)
    if target.id == me.id:
        raise SocialError("cannot_self_friend", "Cannot friend yourself")

    existing = await _find_request_between(session, me.id, target.id)
    if existing is not None:
        if existing.status == FriendRequestStatus.accepted:
            raise SocialError(
                "already_friends", "Already friends", http_status=409
            )
        if existing.status == FriendRequestStatus.pending:
            if existing.from_user_id == target.id:
                # Auto-accept reverse pending request.
                existing.status = FriendRequestStatus.accepted
                existing.responded_at = datetime.now(timezone.utc)
                return existing
            raise SocialError(
                "request_pending",
                "Request already pending",
                http_status=409,
            )
        # declined/cancelled: re-open as a new request.
        existing.status = FriendRequestStatus.pending
        existing.from_user_id = me.id
        existing.to_user_id = target.id
        existing.responded_at = None
        return existing

    request = FriendRequest(
        from_user_id=me.id,
        to_user_id=target.id,
        status=FriendRequestStatus.pending,
    )
    session.add(request)
    await session.flush()
    return request


async def respond_to_friend_request(
    session: AsyncSession,
    *,
    me: User,
    request_id: uuid.UUID,
    accept: bool,
) -> FriendRequest:
    request = await session.get(FriendRequest, request_id)
    if request is None:
        raise SocialError(
            "request_not_found", "Request not found", http_status=404
        )
    if request.to_user_id != me.id:
        raise SocialError("not_recipient", "Not your request", http_status=403)
    if request.status != FriendRequestStatus.pending:
        raise SocialError(
            "request_not_pending",
            f"Request is {request.status.value}",
            http_status=409,
        )
    request.status = (
        FriendRequestStatus.accepted if accept else FriendRequestStatus.declined
    )
    request.responded_at = datetime.now(timezone.utc)
    return request


async def cancel_friend_request(
    session: AsyncSession,
    *,
    me: User,
    request_id: uuid.UUID,
) -> FriendRequest:
    request = await session.get(FriendRequest, request_id)
    if request is None:
        raise SocialError(
            "request_not_found", "Request not found", http_status=404
        )
    if request.from_user_id != me.id:
        raise SocialError("not_sender", "Not your request", http_status=403)
    if request.status != FriendRequestStatus.pending:
        raise SocialError(
            "request_not_pending",
            f"Request is {request.status.value}",
            http_status=409,
        )
    request.status = FriendRequestStatus.cancelled
    request.responded_at = datetime.now(timezone.utc)
    return request


async def unfriend(
    session: AsyncSession, *, me: User, other_user_id: uuid.UUID
) -> None:
    request = await _find_request_between(session, me.id, other_user_id)
    if request is None or request.status != FriendRequestStatus.accepted:
        raise SocialError(
            "not_friends", "Not friends with that user", http_status=404
        )
    await session.delete(request)


async def list_friend_requests(
    session: AsyncSession, me: User
) -> tuple[list[FriendRequest], list[FriendRequest]]:
    incoming_stmt = (
        select(FriendRequest)
        .where(FriendRequest.to_user_id == me.id)
        .where(FriendRequest.status == FriendRequestStatus.pending)
        .order_by(FriendRequest.created_at.desc())
    )
    outgoing_stmt = (
        select(FriendRequest)
        .where(FriendRequest.from_user_id == me.id)
        .where(FriendRequest.status == FriendRequestStatus.pending)
        .order_by(FriendRequest.created_at.desc())
    )
    incoming = list((await session.execute(incoming_stmt)).scalars())
    outgoing = list((await session.execute(outgoing_stmt)).scalars())
    return incoming, outgoing


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------


def _generate_code() -> str:
    return "".join(
        secrets.choice(CHALLENGE_CODE_ALPHABET)
        for _ in range(CHALLENGE_CODE_LENGTH)
    )


@dataclass(frozen=True)
class ChallengeWithChallenger:
    challenge: Challenge
    challenger: User


async def create_challenge(
    session: AsyncSession,
    *,
    challenger: User,
    daily: DailyPuzzle,
    challenger_attempt: RankedAttempt | None = None,
    base_url: str | None = None,
) -> Challenge:
    """Create a share-link for a given daily puzzle.

    Idempotent: if the challenger already has an active challenge for
    this daily puzzle, returns the existing one (refreshed with the
    latest attempt stats).
    """

    stmt = (
        select(Challenge)
        .where(Challenge.challenger_user_id == challenger.id)
        .where(Challenge.daily_puzzle_id == daily.id)
        .where(Challenge.status == ChallengeStatus.active)
    )
    existing = (await session.execute(stmt)).scalars().first()
    if existing is not None:
        if challenger_attempt is not None:
            existing.challenger_attempt_id = challenger_attempt.id
            existing.challenger_duration_ms = (
                challenger_attempt.official_duration_ms
            )
            existing.challenger_mistakes = challenger_attempt.mistakes
        return existing

    code = _generate_code()
    # Cheap collision retry. 36^8 keyspace makes this very rare.
    for _ in range(5):
        clash = await session.execute(select(Challenge).where(Challenge.code == code))
        if clash.scalar_one_or_none() is None:
            break
        code = _generate_code()

    challenge = Challenge(
        code=code,
        challenger_user_id=challenger.id,
        daily_puzzle_id=daily.id,
        challenger_attempt_id=(
            challenger_attempt.id if challenger_attempt is not None else None
        ),
        challenger_duration_ms=(
            challenger_attempt.official_duration_ms
            if challenger_attempt is not None
            else None
        ),
        challenger_mistakes=(
            challenger_attempt.mistakes
            if challenger_attempt is not None
            else None
        ),
        status=ChallengeStatus.active,
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=CHALLENGE_EXPIRY_HOURS),
    )
    session.add(challenge)
    await session.flush()
    return challenge


async def get_challenge_by_code(
    session: AsyncSession, code: str
) -> Challenge | None:
    stmt = select(Challenge).where(Challenge.code == code.upper())
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_challenge(
    session: AsyncSession, challenge_id: uuid.UUID
) -> Challenge | None:
    return await session.get(Challenge, challenge_id)


async def list_acceptances(
    session: AsyncSession, challenge_id: uuid.UUID
) -> list[ChallengeAcceptance]:
    stmt = (
        select(ChallengeAcceptance)
        .where(ChallengeAcceptance.challenge_id == challenge_id)
        .order_by(ChallengeAcceptance.completed_at.asc().nullslast())
    )
    return list((await session.execute(stmt)).scalars())


def _as_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def record_acceptance(
    session: AsyncSession,
    *,
    challenge: Challenge,
    user: User | None,
    guest: GuestSession | None,
    attempt: RankedAttempt | None = None,
) -> ChallengeAcceptance:
    """Persist a recipient outcome for a challenge.

    One row per (challenge, recipient) — re-submissions update in place.
    """

    if user is None and guest is None:
        raise SocialError(
            "auth_required",
            "Sign in or play as guest to accept this challenge",
            http_status=401,
        )

    now = datetime.now(timezone.utc)
    expires_at = _as_aware_utc(challenge.expires_at)
    if challenge.status != ChallengeStatus.active or (
        expires_at is not None and expires_at <= now
    ):
        raise SocialError(
            "challenge_expired",
            "This challenge is no longer active",
            http_status=409,
        )

    if user is not None and user.id == challenge.challenger_user_id:
        raise SocialError(
            "self_challenge",
            "You cannot accept your own challenge",
            http_status=400,
        )

    if attempt is None:
        raise SocialError(
            "attempt_not_complete",
            "Complete today's ranked puzzle before recording this challenge",
            http_status=400,
        )

    if attempt.daily_puzzle_id != challenge.daily_puzzle_id:
        raise SocialError(
            "daily_mismatch",
            "This result is for a different daily puzzle",
            http_status=409,
        )

    if (
        attempt.status not in SUCCESSFUL_CHALLENGE_STATUSES
        or attempt.official_duration_ms is None
    ):
        raise SocialError(
            "attempt_not_complete",
            "Complete today's ranked puzzle before recording this challenge",
            http_status=400,
        )

    stmt = select(ChallengeAcceptance).where(
        ChallengeAcceptance.challenge_id == challenge.id
    )
    if user is not None:
        stmt = stmt.where(ChallengeAcceptance.recipient_user_id == user.id)
    elif guest is not None:
        stmt = stmt.where(
            ChallengeAcceptance.recipient_guest_id == guest.id
        )

    existing = (await session.execute(stmt)).scalars().first()
    if existing is None:
        existing = ChallengeAcceptance(
            challenge_id=challenge.id,
            recipient_user_id=user.id if user else None,
            recipient_guest_id=guest.id if guest else None,
        )
        session.add(existing)
    if attempt is not None:
        existing.attempt_id = attempt.id
        existing.duration_ms = attempt.official_duration_ms
        existing.mistakes = attempt.mistakes
        existing.completed_at = (
            attempt.submitted_at or attempt.validated_at
        )
    await session.flush()
    return existing


async def list_my_challenges(
    session: AsyncSession, me: User
) -> tuple[list[Challenge], list[Challenge]]:
    """Returns (sent, received) — received are unique by challenger."""

    sent_stmt = (
        select(Challenge)
        .where(Challenge.challenger_user_id == me.id)
        .where(Challenge.status == ChallengeStatus.active)
        .order_by(Challenge.created_at.desc())
    )
    sent = list((await session.execute(sent_stmt)).scalars())

    received_stmt = (
        select(Challenge)
        .join(
            ChallengeAcceptance,
            ChallengeAcceptance.challenge_id == Challenge.id,
        )
        .where(ChallengeAcceptance.recipient_user_id == me.id)
        .where(Challenge.status == ChallengeStatus.active)
        .order_by(Challenge.created_at.desc())
    )
    received = list((await session.execute(received_stmt)).scalars())
    return sent, received


__all__ = [
    "CHALLENGE_CODE_LENGTH",
    "CHALLENGE_EXPIRY_HOURS",
    "Relationship",
    "SocialError",
    "cancel_friend_request",
    "create_challenge",
    "get_challenge",
    "get_challenge_by_code",
    "get_friend_ids",
    "list_acceptances",
    "list_friend_requests",
    "list_friends",
    "list_my_challenges",
    "record_acceptance",
    "relationship_with",
    "respond_to_friend_request",
    "search_users",
    "send_friend_request",
    "unfriend",
]
