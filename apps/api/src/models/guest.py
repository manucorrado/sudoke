from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin, UUIDPrimaryKey


class GuestSession(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "guest_sessions"

    # Opaque token the client persists locally to re-identify itself.
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Set when the guest signs up and claims their guest history.
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    claimed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
