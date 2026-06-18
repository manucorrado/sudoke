"""Shared pytest fixtures for the API test suite.

Uses an in-memory SQLite database with `Base.metadata.create_all` instead
of the production Alembic migration (which references Postgres-specific
JSONB types). All ORM models keep their schema portable.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENVIRONMENT", "development")

from src.db.base import Base  # noqa: E402
from src.db.session import get_db  # noqa: E402
from src.main import app  # noqa: E402
from src.middleware.auth import (  # noqa: E402
    AuthenticatedUser,
    optional_auth,
    require_auth,
)
from src.models import User, UserRole  # noqa: E402
from src.services.users import get_or_create_user  # noqa: E402

# Force SQLAlchemy to use the in-memory SQLite DB for tests.
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Per-test DB session — re-creates tables for full isolation."""

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with test_session_factory() as session:
        yield session
        await session.rollback()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        auth_provider_id="admin-principal",
        email="admin@example.com",
        username="admin",
        display_name="Admin",
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def player_user(db_session: AsyncSession) -> User:
    user = User(
        auth_provider_id="player-principal",
        email="player@example.com",
        username="player",
        display_name="Player",
        role=UserRole.player,
    )
    db_session.add(user)
    await db_session.commit()
    return user


def _override_session(session: AsyncSession):
    async def _get() -> AsyncIterator[AsyncSession]:
        yield session

    return _get


def _override_auth(principal: AuthenticatedUser | None):
    async def _resolver() -> AuthenticatedUser | None:
        return principal

    return _resolver


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """API test client backed by the shared session — no Postgres needed."""

    app.dependency_overrides[get_db] = _override_session(db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def login_as(client: AsyncClient, principal: AuthenticatedUser | None) -> None:
    """Override auth deps so subsequent requests see `principal`."""

    app.dependency_overrides[optional_auth] = _override_auth(principal)
    app.dependency_overrides[require_auth] = _override_auth(principal)


def auth_headers() -> dict[str, str]:
    """Stub headers — tokens themselves are mocked via dep overrides."""

    return {"Authorization": "Bearer testtoken"}


__all__ = ["AsyncClient", "auth_headers", "get_or_create_user", "login_as"]
