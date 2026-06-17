"""Principal resolution: authenticated user or guest session.

This is the canonical dependency for route handlers that need to know
"who is acting" without forcing a registered account.

PRD §4 distinguishes Guests (anonymous) from Registered Users. A few endpoints
require auth (ranked submit, leaderboards, etc.); most accept either.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.auth import AuthenticatedUser, optional_auth, require_auth
from src.models import GuestSession, User, UserRole
from src.services.users import get_guest_session_by_token, get_or_create_user

GUEST_HEADER = "X-Guest-Token"


@dataclass(frozen=True)
class Principal:
    """Resolved actor for a request.

    Exactly one of `user` or `guest` is set. `user.is_guest == False` for
    real accounts; guests have `user=None, guest=GuestSession`.
    """

    user: User | None
    guest: GuestSession | None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    @property
    def is_guest(self) -> bool:
        return self.user is None and self.guest is not None


async def get_principal(
    auth: AuthenticatedUser | None = Depends(optional_auth),
    guest_token: str | None = Header(default=None, alias=GUEST_HEADER),
    session: AsyncSession = Depends(get_db),
) -> Principal:
    if auth is not None:
        user = await get_or_create_user(session, auth)
        return Principal(user=user, guest=None)
    if guest_token:
        guest = await get_guest_session_by_token(session, guest_token)
        if guest is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid guest token",
            )
        return Principal(user=None, guest=guest)
    return Principal(user=None, guest=None)


async def require_principal(
    principal: Principal = Depends(get_principal),
) -> Principal:
    if principal.user is None and principal.guest is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication or guest session required",
        )
    return principal


async def require_user(
    auth: AuthenticatedUser = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Forces a registered (non-guest) account."""

    user = await get_or_create_user(session, auth)
    return user


async def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user
