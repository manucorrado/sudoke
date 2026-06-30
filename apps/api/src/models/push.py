"""Push notification device tokens (Epic 8, PRD §19).

Registered users can have one or more Expo push tokens (one per device).
The dispatch service reads this registry to deliver reminders, challenge
alerts, and final-ranking pings. Delivery itself is gated behind config +
APNs/FCM credentials; this table is just the device registry.

`token` is globally unique: re-registering an existing token reassigns
the device to the current account (handles reinstall / account hand-off).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin, UUIDPrimaryKey


class PushToken(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "push_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unknown"
    )


__all__ = ["PushToken"]
