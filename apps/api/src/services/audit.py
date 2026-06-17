from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AdminAuditLog, User


async def record_audit(
    session: AsyncSession,
    *,
    actor: User | None,
    action: str,
    target_type: str | None,
    target_id: str | None,
    payload: dict | None = None,
) -> AdminAuditLog:
    entry = AdminAuditLog(
        actor_user_id=actor.id if actor else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
    )
    session.add(entry)
    return entry
