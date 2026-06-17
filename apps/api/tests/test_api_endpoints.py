from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.auth import AuthenticatedUser
from src.models import User
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


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_guest_session(client: AsyncClient) -> None:
    res = await client.post(
        "/api/v1/guest/sessions",
        json={"locale": "en-US"},
    )
    assert res.status_code == 201
    body = res.json()
    assert "token" in body
    assert len(body["token"]) > 16


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    res = await client.get("/api/v1/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_with_auth(
    client: AsyncClient, player_user: User
) -> None:
    login_as(
        client,
        AuthenticatedUser(user_id=player_user.auth_provider_id, email=player_user.email),
    )
    res = await client.get("/api/v1/me", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["username"] == "player"


@pytest.mark.asyncio
async def test_admin_import_and_schedule_flow(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    login_as(
        client,
        AuthenticatedUser(user_id=admin_user.auth_provider_id, email=admin_user.email),
    )

    res = await client.post(
        "/api/v1/admin/puzzles/import",
        json={
            "givens": EASY,
            "solution": EASY_SOL,
            "difficulty": "easy",
            "estimated_min_seconds": 180,
            "estimated_max_seconds": 360,
            "source": "manual",
            "license": "CC0",
        },
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    [puzzle] = res.json()
    puzzle_id = puzzle["id"]
    assert puzzle["status"] == "needs_review"

    res = await client.post(
        f"/api/v1/admin/puzzles/{puzzle_id}/approve",
        json={"review_notes": "looks good"},
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "approved"

    res = await client.post(
        "/api/v1/admin/daily-puzzles/bulk-schedule",
        json={"entries": [{"puzzle_id": puzzle_id, "scheduled_for": str(date(2026, 6, 18))}]},
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    assert len(res.json()) == 1


@pytest.mark.asyncio
async def test_non_admin_cannot_import(
    client: AsyncClient, player_user: User
) -> None:
    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id, email=player_user.email
        ),
    )
    res = await client.post(
        "/api/v1/admin/puzzles/import",
        json={
            "givens": EASY,
            "difficulty": "easy",
            "estimated_min_seconds": 180,
            "estimated_max_seconds": 360,
            "source": "manual",
            "license": "CC0",
        },
        headers=auth_headers(),
    )
    assert res.status_code == 403
