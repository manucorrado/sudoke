"""Push token registration + preference-aware dispatch (Epic 8)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.auth import AuthenticatedUser
from src.models import NotificationPreference, PushToken, User, UserRole
from src.services.notifications import PushMessage, dispatch_to_users
from tests.conftest import auth_headers, login_as


@pytest.mark.asyncio
async def test_register_push_token(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id, email=player_user.email
        ),
    )
    res = await client.post(
        "/api/v1/me/push-tokens",
        json={"token": "ExponentPushToken[abc]", "platform": "ios"},
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["token"] == "ExponentPushToken[abc]"
    assert body["platform"] == "ios"

    rows = (
        await db_session.execute(
            select(PushToken).where(PushToken.token == "ExponentPushToken[abc]")
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].user_id == player_user.id


@pytest.mark.asyncio
async def test_register_push_token_idempotent(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id, email=player_user.email
        ),
    )
    await client.post(
        "/api/v1/me/push-tokens",
        json={"token": "tok-1", "platform": "ios"},
        headers=auth_headers(),
    )
    res = await client.post(
        "/api/v1/me/push-tokens",
        json={"token": "tok-1", "platform": "android"},
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    assert res.json()["platform"] == "android"

    rows = (
        await db_session.execute(
            select(PushToken).where(PushToken.token == "tok-1")
        )
    ).scalars().all()
    assert len(rows) == 1  # updated in place, not duplicated


@pytest.mark.asyncio
async def test_unregister_push_token(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id, email=player_user.email
        ),
    )
    await client.post(
        "/api/v1/me/push-tokens",
        json={"token": "tok-del", "platform": "ios"},
        headers=auth_headers(),
    )
    res = await client.delete(
        "/api/v1/me/push-tokens?token=tok-del", headers=auth_headers()
    )
    assert res.status_code == 204, res.text

    rows = (
        await db_session.execute(
            select(PushToken).where(PushToken.token == "tok-del")
        )
    ).scalars().all()
    assert rows == []


class _FakeSender:
    def __init__(self) -> None:
        self.sent: list[PushMessage] = []

    async def send(self, messages: list[PushMessage]) -> None:
        self.sent.extend(messages)


@pytest.mark.asyncio
async def test_dispatch_respects_prefs_and_tokens(
    db_session: AsyncSession,
) -> None:
    # A: opted in (no prefs row -> default on) + token -> notified
    # B: opted out (final_ranking_ready=False) + token -> skipped
    # C: opted in but no device -> skipped
    a = User(auth_provider_id="disp-a", username="a", role=UserRole.player)
    b = User(auth_provider_id="disp-b", username="b", role=UserRole.player)
    c = User(auth_provider_id="disp-c", username="c", role=UserRole.player)
    db_session.add_all([a, b, c])
    await db_session.flush()

    db_session.add_all(
        [
            PushToken(user_id=a.id, token="tokA", platform="ios"),
            PushToken(user_id=b.id, token="tokB", platform="android"),
            NotificationPreference(user_id=b.id, final_ranking_ready=False),
        ]
    )
    await db_session.commit()

    sender = _FakeSender()
    messages = await dispatch_to_users(
        db_session,
        user_ids=[a.id, b.id, c.id],
        notif_type="final_ranking_ready",
        title="Final results are in",
        body="See where you placed.",
        data={"daily_puzzle_id": "d-1"},
        sender=sender,
    )

    assert {m.to for m in messages} == {"tokA"}
    assert len(sender.sent) == 1
    assert sender.sent[0].data["type"] == "final_ranking_ready"
    assert sender.sent[0].data["daily_puzzle_id"] == "d-1"


@pytest.mark.asyncio
async def test_dispatch_noop_without_recipients(
    db_session: AsyncSession,
) -> None:
    sender = _FakeSender()
    messages = await dispatch_to_users(
        db_session,
        user_ids=[],
        notif_type="daily_reminder",
        title="t",
        body="b",
        sender=sender,
    )
    assert messages == []
    assert sender.sent == []
