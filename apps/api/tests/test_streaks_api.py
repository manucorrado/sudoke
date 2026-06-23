"""Streak + notification preferences (Epic 8)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.auth import AuthenticatedUser
from src.models import User
from src.services.streaks import (
    FREEZES_PER_COMPLETIONS,
    MAX_FREEZES_HELD,
    record_completion,
    sync_to_today,
)
from tests.conftest import auth_headers, login_as


@pytest.mark.asyncio
async def test_record_completion_extends_streak(
    db_session: AsyncSession, player_user: User
) -> None:
    today = date(2026, 6, 10)
    s = await record_completion(db_session, player_user, completed_on=today)
    assert s.current_length == 1
    assert s.longest_length == 1
    assert s.last_completed_date == today

    s = await record_completion(
        db_session, player_user, completed_on=today + timedelta(days=1)
    )
    assert s.current_length == 2

    # idempotent
    s = await record_completion(
        db_session, player_user, completed_on=today + timedelta(days=1)
    )
    assert s.current_length == 2


@pytest.mark.asyncio
async def test_freeze_earn_caps_at_two(
    db_session: AsyncSession, player_user: User
) -> None:
    today = date(2026, 6, 1)
    for i in range(FREEZES_PER_COMPLETIONS * 3 + 1):
        await record_completion(
            db_session, player_user, completed_on=today + timedelta(days=i)
        )
    s = await record_completion(
        db_session, player_user, completed_on=today + timedelta(days=22)
    )
    assert s.freezes_held == MAX_FREEZES_HELD


@pytest.mark.asyncio
async def test_freeze_auto_consumed_on_miss(
    db_session: AsyncSession, player_user: User
) -> None:
    today = date(2026, 6, 1)
    # 7 completions to earn 1 freeze
    for i in range(FREEZES_PER_COMPLETIONS):
        await record_completion(
            db_session, player_user, completed_on=today + timedelta(days=i)
        )
    s = await sync_to_today(
        db_session,
        player_user,
        today=today + timedelta(days=FREEZES_PER_COMPLETIONS),
    )
    # Last completed was day 6, calling on day 7 = not missed yet.
    assert s.freezes_held == 1
    assert s.current_length == FREEZES_PER_COMPLETIONS

    # Skip a day; freeze should auto-consume on the second sync.
    s = await sync_to_today(
        db_session,
        player_user,
        today=today + timedelta(days=FREEZES_PER_COMPLETIONS + 1),
    )
    assert s.freezes_held == 0
    assert s.current_length == FREEZES_PER_COMPLETIONS

    # Now skip another day with no freezes — streak breaks.
    s = await sync_to_today(
        db_session,
        player_user,
        today=today + timedelta(days=FREEZES_PER_COMPLETIONS + 5),
    )
    assert s.current_length == 0


@pytest.mark.asyncio
async def test_me_streak_endpoint(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id,
            email=player_user.email,
        ),
    )
    res = await client.get("/api/v1/me/streak", headers=auth_headers())
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["current_length"] == 0
    assert body["max_freezes"] == MAX_FREEZES_HELD


@pytest.mark.asyncio
async def test_notification_preferences_round_trip(
    client: AsyncClient, db_session: AsyncSession, player_user: User
) -> None:
    login_as(
        client,
        AuthenticatedUser(
            user_id=player_user.auth_provider_id, email=player_user.email
        ),
    )
    res = await client.get(
        "/api/v1/me/notifications/preferences", headers=auth_headers()
    )
    assert res.status_code == 200
    body = res.json()
    assert body["daily_reminder"] is True

    res = await client.patch(
        "/api/v1/me/notifications/preferences",
        json={"daily_reminder": False, "beat_your_time": False},
        headers=auth_headers(),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["daily_reminder"] is False
    assert body["beat_your_time"] is False
    assert body["friend_challenged_you"] is True
