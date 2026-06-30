"""User & guest session helpers."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.models import (
    ChallengeAcceptance,
    GuestSession,
    RankedAttempt,
    User,
    UserRole,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.middleware.auth import AuthenticatedUser
    from src.schemas.common import UpdateProfileRequest


class GuestClaimError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


async def get_or_create_user(
    session: AsyncSession, principal: AuthenticatedUser
) -> User:
    """Idempotently materialize the user record for the given JWT principal."""

    result = await session.execute(
        select(User).where(User.auth_provider_id == principal.user_id)
    )
    user = result.scalar_one_or_none()
    if user is not None:
        if principal.email and user.email != principal.email:
            user.email = principal.email
        return user
    user = User(
        auth_provider_id=principal.user_id,
        email=principal.email,
        role=UserRole.player,
        is_guest=False,
    )
    session.add(user)
    await session.flush()
    return user


async def update_profile(
    session: AsyncSession, user: User, payload: UpdateProfileRequest
) -> User:
    if payload.username is not None:
        existing = await session.execute(
            select(User)
            .where(User.username == payload.username)
            .where(User.id != user.id)
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("username_taken")
        user.username = payload.username
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    return user


async def create_guest_session(
    session: AsyncSession, *, user_agent: str | None, locale: str | None
) -> GuestSession:
    token = secrets.token_urlsafe(32)
    guest = GuestSession(token=token, user_agent=user_agent, locale=locale)
    session.add(guest)
    await session.flush()
    return guest


async def get_guest_session_by_token(
    session: AsyncSession, token: str
) -> GuestSession | None:
    result = await session.execute(
        select(GuestSession).where(GuestSession.token == token)
    )
    return result.scalar_one_or_none()


async def claim_guest_session(
    session: AsyncSession, *, user: User, guest_token: str
) -> User:
    guest = await get_guest_session_by_token(session, guest_token)
    if guest is None:
        raise GuestClaimError(
            "guest_not_found", "Guest session not found", http_status=401
        )
    if (
        guest.claimed_by_user_id is not None
        and guest.claimed_by_user_id != user.id
    ):
        raise GuestClaimError(
            "guest_already_claimed",
            "Guest session is already claimed",
            http_status=409,
        )

    now = datetime.now(UTC)
    if guest.claimed_by_user_id is None:
        guest.claimed_by_user_id = user.id
    if guest.claimed_at is None:
        guest.claimed_at = now
    if user.claimed_from_guest_id is None:
        user.claimed_from_guest_id = guest.id

    await _claim_challenge_acceptances(session, user=user, guest=guest)
    await _claim_ranked_attempts(session, user=user, guest=guest)
    await session.flush()
    return user


async def _claim_challenge_acceptances(
    session: AsyncSession, *, user: User, guest: GuestSession
) -> None:
    stmt = select(ChallengeAcceptance).where(
        ChallengeAcceptance.recipient_guest_id == guest.id
    )
    acceptances = list((await session.execute(stmt)).scalars())
    for acceptance in acceptances:
        if (
            acceptance.recipient_user_id is None
            or acceptance.recipient_user_id == user.id
        ):
            acceptance.recipient_user_id = user.id


async def _claim_ranked_attempts(
    session: AsyncSession, *, user: User, guest: GuestSession
) -> None:
    user_daily_stmt = select(RankedAttempt.daily_puzzle_id).where(
        RankedAttempt.user_id == user.id
    )
    claimed_daily_ids = set((await session.execute(user_daily_stmt)).scalars())

    guest_attempt_stmt = (
        select(RankedAttempt)
        .where(RankedAttempt.guest_session_id == guest.id)
        .order_by(RankedAttempt.created_at.asc())
    )
    guest_attempts = list((await session.execute(guest_attempt_stmt)).scalars())
    for attempt in guest_attempts:
        if attempt.user_id == user.id:
            claimed_daily_ids.add(attempt.daily_puzzle_id)
            continue
        if attempt.user_id is not None:
            continue
        if attempt.daily_puzzle_id in claimed_daily_ids:
            continue
        attempt.user_id = user.id
        claimed_daily_ids.add(attempt.daily_puzzle_id)
