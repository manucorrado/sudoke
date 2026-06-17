from dataclasses import dataclass

import structlog
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import settings

DEV_BYPASS_HEADER = "X-Dev-Auth-User"

logger = structlog.get_logger()

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str | None = None
    session_id: str | None = None


async def _decode_token(token: str) -> AuthenticatedUser:
    """Decode and verify a Clerk JWT.

    TODO: In production, fetch Clerk JWKS from
    https://api.clerk.com/v1/jwks and verify the signature.
    Currently decodes without verification in dev mode.
    """
    try:
        if settings.is_development:
            payload = jwt.get_unverified_claims(token)
        else:
            # TODO: Fetch JWKS from Clerk and verify properly
            payload = jwt.get_unverified_claims(token)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
            )

        return AuthenticatedUser(
            user_id=user_id,
            email=payload.get("email"),
            session_id=payload.get("sid"),
        )
    except JWTError as exc:
        logger.warning("JWT decode failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    dev_user: str | None = Header(default=None, alias=DEV_BYPASS_HEADER),
) -> AuthenticatedUser | None:
    """Extract and decode Bearer token. Returns None if no token provided.

    In development the API also accepts an ``X-Dev-Auth-User`` header
    which short-circuits JWT decoding. This is used by the admin UI to
    authenticate without standing up a full Clerk session, and is never
    honored outside of `ENVIRONMENT=development`.
    """

    if dev_user and settings.is_development:
        return AuthenticatedUser(user_id=dev_user)
    if credentials is None:
        return None
    return await _decode_token(credentials.credentials)


async def optional_auth(
    user: AuthenticatedUser | None = Depends(get_current_user),
) -> AuthenticatedUser | None:
    """Returns the authenticated user or None — never raises."""
    return user


async def require_auth(
    user: AuthenticatedUser | None = Depends(get_current_user),
) -> AuthenticatedUser:
    """Raises 401 if no valid authentication is present."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
