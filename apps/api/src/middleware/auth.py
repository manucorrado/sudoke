from dataclasses import dataclass
from time import monotonic
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import structlog
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import settings

DEV_BYPASS_HEADER = "X-Dev-Auth-User"

logger = structlog.get_logger()

bearer_scheme = HTTPBearer(auto_error=False)
JWKS_CACHE_TTL_SECONDS = 300
JWKS_FETCH_TIMEOUT_SECONDS = 5
JWKS_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str | None = None
    session_id: str | None = None


async def _decode_token(token: str) -> AuthenticatedUser:
    """Decode and verify a Clerk JWT.

    Development keeps the existing bearer-token shortcut so local flows can
    run without Clerk. Staging/production must verify against Clerk JWKS.
    """
    try:
        if settings.is_development:
            payload = jwt.get_unverified_claims(token)
        else:
            payload = await _verify_clerk_token(token)

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
    except HTTPException:
        raise
    except JWTError as exc:
        logger.warning("JWT decode failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc


def _unauthorized(detail: str = "Invalid authentication token") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def _verify_clerk_token(token: str) -> dict[str, Any]:
    jwks_url = settings.clerk_jwks_url
    if not jwks_url:
        logger.error("Clerk JWT verification is not configured")
        raise _unauthorized("Authentication is not configured")

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    alg = header.get("alg")
    if not isinstance(kid, str) or not isinstance(alg, str):
        raise _unauthorized()
    if alg != "RS256":
        raise _unauthorized()

    jwks = await _get_jwks(jwks_url)
    signing_key = _select_jwk(jwks, kid=kid)
    if signing_key is None:
        raise _unauthorized()

    options = {"verify_aud": settings.CLERK_JWT_AUDIENCE is not None}
    decode_kwargs: dict[str, Any] = {
        "key": signing_key,
        "algorithms": ["RS256"],
        "options": options,
    }
    if settings.CLERK_ISSUER:
        decode_kwargs["issuer"] = settings.CLERK_ISSUER
    if settings.CLERK_JWT_AUDIENCE:
        decode_kwargs["audience"] = settings.CLERK_JWT_AUDIENCE
    return jwt.decode(token, **decode_kwargs)


async def _get_jwks(url: str) -> dict[str, Any]:
    now = monotonic()
    cached = JWKS_CACHE.get(url)
    if cached and now - cached[0] < JWKS_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        jwks = await _fetch_jwks(url)
    except (OSError, URLError, ValueError) as exc:
        logger.warning("Clerk JWKS fetch failed", error=str(exc))
        raise _unauthorized("Authentication provider unavailable") from exc

    JWKS_CACHE[url] = (now, jwks)
    return jwks


async def _fetch_jwks(url: str) -> dict[str, Any]:
    import asyncio
    import json

    def _read() -> dict[str, Any]:
        with urlopen(url, timeout=JWKS_FETCH_TIMEOUT_SECONDS) as response:
            payload = response.read()
        parsed = json.loads(payload.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("JWKS response was not an object")
        return parsed

    return await asyncio.to_thread(_read)


def _select_jwk(jwks: dict[str, Any], *, kid: str) -> dict[str, Any] | None:
    keys = jwks.get("keys")
    if not isinstance(keys, list):
        return None
    for key in keys:
        if isinstance(key, dict) and key.get("kid") == kid:
            return key
    return None


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
