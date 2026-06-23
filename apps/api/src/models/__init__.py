"""SQLAlchemy ORM models for Sudoke.

Importing this package registers every model with `Base.metadata` so
Alembic auto-generation and `Base.metadata.create_all` see them.
"""

from src.models.attempts import (
    AttemptEventType,
    AttemptStatus,
    RankedAttempt,
    RankedAttemptEvent,
)
from src.models.audit import AdminAuditLog
from src.models.guest import GuestSession
from src.models.puzzles import DailyPuzzle, DailyPuzzleStatus, Puzzle, PuzzleStatus
from src.models.rating import DailyResult, RatingHistory, UserRating
from src.models.social import (
    Challenge,
    ChallengeAcceptance,
    ChallengeStatus,
    FriendRequest,
    FriendRequestStatus,
)
from src.models.streaks import NotificationPreference, UserStreak
from src.models.users import User, UserRole

__all__ = [
    "AdminAuditLog",
    "AttemptEventType",
    "AttemptStatus",
    "Challenge",
    "ChallengeAcceptance",
    "ChallengeStatus",
    "DailyPuzzle",
    "DailyPuzzleStatus",
    "DailyResult",
    "FriendRequest",
    "FriendRequestStatus",
    "GuestSession",
    "NotificationPreference",
    "Puzzle",
    "PuzzleStatus",
    "RankedAttempt",
    "RankedAttemptEvent",
    "RatingHistory",
    "User",
    "UserRating",
    "UserRole",
    "UserStreak",
]
