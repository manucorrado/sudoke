"""User & guest session helpers."""

from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.auth import AuthenticatedUser
from src.models import GuestSession, User, UserRole
from src.schemas.common import UpdateProfileRequest


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
            select(User).where(User.username == payload.username).where(User.id != user.id)
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
