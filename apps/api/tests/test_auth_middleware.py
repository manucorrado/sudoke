from __future__ import annotations

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from jose.utils import base64url_encode

from src.config import settings
from src.middleware import auth as auth_module
from src.middleware.auth import _decode_token, get_current_user


def _rsa_public_jwk(key: rsa.RSAPrivateKey, *, kid: str) -> dict[str, str]:
    public_numbers = key.public_key().public_numbers()
    exponent = public_numbers.e.to_bytes(
        (public_numbers.e.bit_length() + 7) // 8,
        "big",
    )
    modulus = public_numbers.n.to_bytes(
        (public_numbers.n.bit_length() + 7) // 8,
        "big",
    )
    return {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
        "e": base64url_encode(exponent).decode("ascii"),
        "n": base64url_encode(modulus).decode("ascii"),
    }


def _private_pem(key: rsa.RSAPrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")


@pytest.fixture(autouse=True)
def reset_auth_settings(monkeypatch: pytest.MonkeyPatch):
    auth_module.JWKS_CACHE.clear()
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "CLERK_JWKS_URL", None)
    monkeypatch.setattr(settings, "CLERK_ISSUER", None)
    monkeypatch.setattr(settings, "CLERK_JWT_AUDIENCE", None)
    yield
    auth_module.JWKS_CACHE.clear()


@pytest.mark.asyncio
async def test_development_accepts_unverified_bearer_token() -> None:
    token = jwt.encode({"sub": "user_dev", "email": "dev@example.com"}, "dev-secret")

    user = await _decode_token(token)

    assert user.user_id == "user_dev"
    assert user.email == "dev@example.com"


@pytest.mark.asyncio
async def test_dev_bypass_header_is_ignored_outside_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")

    user = await get_current_user(credentials=None, dev_user="dev-user")

    assert user is None


@pytest.mark.asyncio
async def test_staging_rejects_bearer_when_clerk_jwks_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    token = jwt.encode({"sub": "user_123"}, "dev-secret")

    with pytest.raises(HTTPException) as exc:
        await _decode_token(token)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_staging_verifies_clerk_rs256_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issuer = "https://example.clerk.accounts.dev"
    kid = "test-key"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwks = {"keys": [_rsa_public_jwk(key, kid=kid)]}
    token = jwt.encode(
        {"sub": "user_123", "email": "user@example.com", "iss": issuer},
        _private_pem(key),
        algorithm="RS256",
        headers={"kid": kid},
    )

    async def fake_get_jwks(url: str) -> dict[str, object]:
        assert url == f"{issuer}/.well-known/jwks.json"
        return jwks

    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "CLERK_ISSUER", issuer)
    monkeypatch.setattr(auth_module, "_get_jwks", fake_get_jwks)

    user = await _decode_token(token)

    assert user.user_id == "user_123"
    assert user.email == "user@example.com"


@pytest.mark.asyncio
async def test_staging_rejects_forged_hs256_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "CLERK_ISSUER", "https://example.clerk.accounts.dev")
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=jwt.encode({"sub": "user_123"}, "attacker-secret"),
    )

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=credentials, dev_user=None)

    assert exc.value.status_code == 401
