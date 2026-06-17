from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from src.models.guest import GuestSession


class UserRole(str, enum.Enum):
    player = "player"
    admin = "admin"


class User(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "users"

    # External auth subject (e.g. Clerk user id). Nullable for guests.
    auth_provider_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(
        String(32), unique=True, nullable=True, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.player, nullable=False
    )
    is_guest: Mapped[bool] = mapped_column(default=False, nullable=False)

    # When a guest signs up, we link the new account back to the original guest.
    claimed_from_guest_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "guest_sessions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_users_claimed_from_guest_id",
        ),
        nullable=True,
    )

    guest_session: Mapped[GuestSession | None] = relationship(
        "GuestSession",
        foreign_keys=[claimed_from_guest_id],
        lazy="raise",
    )
