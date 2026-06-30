"""Push notification registry + dispatch (Epic 8, PRD §19).

The dispatcher is preference-aware: each notification type maps 1:1 onto a
`NotificationPreference` flag, and users who opted out (or have no
registered device) are skipped. Delivery uses Expo's push HTTP API and is
gated by `settings.push_enabled` — off by default, so the dispatcher is a
safe no-op until APNs/FCM credentials are configured. Sending goes through
an injectable `PushSender` so tests never touch the network.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, Protocol
from urllib.request import Request, urlopen

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import NotificationPreference, PushToken, User

logger = structlog.get_logger()

NotificationType = Literal[
    "daily_reminder",
    "friend_challenged_you",
    "beat_your_time",
    "final_ranking_ready",
]

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
EXPO_BATCH_SIZE = 100


@dataclass(frozen=True)
class PushMessage:
    to: str
    title: str
    body: str
    data: dict[str, str]


class PushSender(Protocol):
    async def send(self, messages: list[PushMessage]) -> None: ...


class NullPushSender:
    """Default sender — performs no I/O (push disabled)."""

    async def send(self, messages: list[PushMessage]) -> None:
        if messages:
            logger.info("push_disabled_skipped", count=len(messages))


class ExpoPushSender:
    """Posts messages to Expo's push service in batches (network I/O)."""

    def __init__(self, access_token: str | None = None) -> None:
        self._access_token = access_token

    async def send(self, messages: list[PushMessage]) -> None:
        for start in range(0, len(messages), EXPO_BATCH_SIZE):
            batch = messages[start : start + EXPO_BATCH_SIZE]
            payload = json.dumps(
                [
                    {"to": m.to, "title": m.title, "body": m.body, "data": m.data}
                    for m in batch
                ]
            ).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if self._access_token:
                headers["Authorization"] = f"Bearer {self._access_token}"
            request = Request(EXPO_PUSH_URL, data=payload, headers=headers)
            await asyncio.to_thread(
                lambda r=request: urlopen(r, timeout=10).read()  # noqa: S310
            )


def get_push_sender() -> PushSender:
    if settings.push_enabled:
        return ExpoPushSender(settings.EXPO_ACCESS_TOKEN)
    return NullPushSender()


async def register_push_token(
    session: AsyncSession, user: User, *, token: str, platform: str
) -> PushToken:
    """Idempotent upsert keyed on the (globally unique) token.

    Re-registering reassigns the token to the current user and refreshes
    its platform — handling reinstall / account hand-off on a device.
    """

    existing = (
        await session.execute(select(PushToken).where(PushToken.token == token))
    ).scalar_one_or_none()
    if existing is not None:
        existing.user_id = user.id
        existing.platform = platform
        return existing
    row = PushToken(user_id=user.id, token=token, platform=platform)
    session.add(row)
    await session.flush()
    return row


async def remove_push_token(
    session: AsyncSession, user: User, *, token: str
) -> bool:
    result = await session.execute(
        delete(PushToken)
        .where(PushToken.token == token)
        .where(PushToken.user_id == user.id)
    )
    return (result.rowcount or 0) > 0


async def _tokens_for_users(
    session: AsyncSession, user_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[str]]:
    if not user_ids:
        return {}
    rows = (
        await session.execute(
            select(PushToken).where(PushToken.user_id.in_(user_ids))
        )
    ).scalars()
    out: dict[uuid.UUID, list[str]] = {}
    for row in rows:
        out.setdefault(row.user_id, []).append(row.token)
    return out


async def _opted_in(
    session: AsyncSession,
    user_ids: list[uuid.UUID],
    notif_type: NotificationType,
) -> set[uuid.UUID]:
    """User ids that allow `notif_type`.

    A missing preferences row means the user hasn't customized settings,
    and every flag defaults to True — so they're opted in.
    """

    if not user_ids:
        return set()
    rows = (
        await session.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id.in_(user_ids)
            )
        )
    ).scalars()
    prefs = {r.user_id: r for r in rows}
    return {
        uid
        for uid in user_ids
        if uid not in prefs or bool(getattr(prefs[uid], notif_type))
    }


async def dispatch_to_users(
    session: AsyncSession,
    *,
    user_ids: Iterable[uuid.UUID],
    notif_type: NotificationType,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
    sender: PushSender | None = None,
) -> list[PushMessage]:
    """Build + send messages for opted-in users that have a device.

    Returns the messages sent (handy for tests + metrics). Honors each
    user's preference flag for `notif_type` and skips users with no token.
    """

    ids = list(dict.fromkeys(user_ids))  # de-dup, preserve order
    if not ids:
        return []
    allowed = await _opted_in(session, ids, notif_type)
    tokens = await _tokens_for_users(session, [u for u in ids if u in allowed])
    payload = {**(data or {}), "type": notif_type}
    messages = [
        PushMessage(to=token, title=title, body=body, data=payload)
        for uid in ids
        if uid in allowed
        for token in tokens.get(uid, [])
    ]
    if messages:
        await (sender or get_push_sender()).send(messages)
    return messages


__all__ = [
    "EXPO_PUSH_URL",
    "ExpoPushSender",
    "NotificationType",
    "NullPushSender",
    "PushMessage",
    "PushSender",
    "dispatch_to_users",
    "get_push_sender",
    "register_push_token",
    "remove_push_token",
]
