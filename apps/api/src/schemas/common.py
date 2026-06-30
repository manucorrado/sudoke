from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.models import (
    AttemptEventType,
    AttemptStatus,
    DailyPuzzleStatus,
    PuzzleStatus,
    UserRole,
)
from src.models.puzzles import PuzzleDifficulty


class APIModel(BaseModel):
    """Base for response models — read from ORM and emit snake_case JSON."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserPublic(APIModel):
    id: uuid.UUID
    username: str | None
    display_name: str | None
    avatar_url: str | None
    role: UserRole
    is_guest: bool


class MeResponse(UserPublic):
    email: str | None
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=32)
    display_name: str | None = Field(default=None, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=1024)


class CreateGuestRequest(BaseModel):
    user_agent: str | None = None
    locale: str | None = None


class GuestSessionResponse(APIModel):
    id: uuid.UUID
    token: str
    created_at: datetime


class PuzzleAdminCreate(BaseModel):
    givens: str = Field(min_length=81, max_length=81)
    solution: str | None = Field(default=None, min_length=81, max_length=81)
    difficulty: PuzzleDifficulty
    estimated_min_seconds: int = Field(ge=30, le=7200)
    estimated_max_seconds: int = Field(ge=30, le=14400)
    source: str | None = Field(default=None, max_length=255)
    license: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class PuzzleAdminBulkImport(BaseModel):
    puzzles: list[PuzzleAdminCreate]


class PuzzleAdminResponse(APIModel):
    id: uuid.UUID
    givens: str
    solution: str
    difficulty: PuzzleDifficulty
    status: PuzzleStatus
    estimated_min_seconds: int
    estimated_max_seconds: int
    clue_count: int
    source: str | None
    license: str | None
    notes: str | None
    reviewer_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime
    updated_at: datetime


class PuzzleReviewRequest(BaseModel):
    review_notes: str | None = None


class PlaytestRequest(BaseModel):
    duration_ms: int = Field(ge=0)
    mistakes: int = Field(ge=0)
    notes: str | None = None


class BulkScheduleEntry(BaseModel):
    puzzle_id: uuid.UUID
    scheduled_for: date


class BulkScheduleRequest(BaseModel):
    entries: list[BulkScheduleEntry]


class DailyPuzzleAdminResponse(APIModel):
    id: uuid.UUID
    puzzle_id: uuid.UUID
    scheduled_for: date
    activate_at: datetime
    finalize_at: datetime
    status: DailyPuzzleStatus
    difficulty: PuzzleDifficulty | None = None


class DailyPuzzlePublic(APIModel):
    """What the client sees on /daily/current.

    NOTE: solution is intentionally absent.
    """

    id: uuid.UUID
    scheduled_for: date
    activate_at: datetime
    finalize_at: datetime
    difficulty: PuzzleDifficulty
    estimated_min_seconds: int
    estimated_max_seconds: int
    givens: str


class AttemptResponse(APIModel):
    id: uuid.UUID
    daily_puzzle_id: uuid.UUID
    status: AttemptStatus
    previewed_at: datetime | None
    started_at: datetime | None
    submitted_at: datetime | None
    abandoned_at: datetime | None
    mistakes: int
    official_duration_ms: int | None
    under_review_reason: str | None


class SubmitAttemptRequest(BaseModel):
    submitted_grid: str = Field(min_length=81, max_length=81)
    mistakes: int = Field(ge=0)


class AttemptEventCreate(BaseModel):
    event_type: AttemptEventType
    client_ts: datetime | None = None
    payload: dict | None = None


class AttemptEventBatch(BaseModel):
    events: list[AttemptEventCreate]


class AttemptEventResponse(APIModel):
    id: uuid.UUID
    event_type: AttemptEventType
    occurred_at: datetime
    client_ts: datetime | None
    payload: dict | None


class ErrorResponse(BaseModel):
    detail: str
    issues: list[str] | None = None


class RatingPublic(APIModel):
    """Snapshot of a user's current rating (`GET /me/rating`)."""

    rating: int
    tier: str
    provisional_completions: int
    is_provisional: bool
    calculation_version: str
    last_updated_at: datetime | None


class RatingHistoryEntry(APIModel):
    daily_puzzle_id: uuid.UUID
    attempt_id: uuid.UUID
    kind: str
    old_rating: int
    new_rating: int
    delta: int
    percentile: float | None
    cohort_size: int
    was_provisional: bool
    calculation_version: str
    applied_at: datetime


class RatingHistoryResponse(BaseModel):
    entries: list[RatingHistoryEntry]


class LeaderboardRowPublic(BaseModel):
    rank: int
    user_id: uuid.UUID
    username: str | None
    display_name: str | None
    avatar_url: str | None
    official_duration_ms: int
    mistakes: int
    rating: int
    rating_delta: int | None
    tier: str
    is_me: bool


class LeaderboardResponsePublic(BaseModel):
    daily_puzzle_id: uuid.UUID
    view: str
    cohort_size: int
    is_final: bool
    rows: list[LeaderboardRowPublic]


class MyResultPublic(BaseModel):
    daily_puzzle_id: uuid.UUID
    attempt_id: uuid.UUID
    status: AttemptStatus
    rank: int | None
    cohort_size: int
    percentile: float | None
    mistakes: int
    official_duration_ms: int | None
    rating_before: int | None
    rating_after: int | None
    rating_delta: int | None
    was_provisional: bool
    tier: str | None
    is_final: bool


class StreakPublic(APIModel):
    current_length: int
    longest_length: int
    freezes_held: int
    max_freezes: int
    completions_total: int
    last_completed_date: date | None
    streak_started_date: date | None


class NotificationPreferencesPublic(APIModel):
    daily_reminder: bool
    friend_challenged_you: bool
    beat_your_time: bool
    final_ranking_ready: bool


class UpdateNotificationPreferencesRequest(BaseModel):
    daily_reminder: bool | None = None
    friend_challenged_you: bool | None = None
    beat_your_time: bool | None = None
    final_ranking_ready: bool | None = None


class RegisterPushTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=256)
    platform: Literal["ios", "android", "web"] = "ios"


class PushTokenPublic(APIModel):
    token: str
    platform: str


# ---- Epic 7 — Archive / practice ----------------------------------------


class ArchiveEntryPublic(APIModel):
    daily_puzzle_id: uuid.UUID
    puzzle_id: uuid.UUID
    scheduled_for: date
    difficulty: PuzzleDifficulty
    estimated_min_seconds: int
    estimated_max_seconds: int
    is_final: bool


class ArchiveListPublic(BaseModel):
    entries: list[ArchiveEntryPublic]


class ArchiveDetailPublic(APIModel):
    daily_puzzle_id: uuid.UUID
    puzzle_id: uuid.UUID
    scheduled_for: date
    difficulty: PuzzleDifficulty
    estimated_min_seconds: int
    estimated_max_seconds: int
    givens: str
    solution: str
    is_final: bool


class ArchiveMyResultPublic(BaseModel):
    """The caller's original ranked result for a closed daily (PRD §12).

    `played=False` (and `result=None`) when the caller never made a ranked
    attempt for this daily — the archive UI shows the historical board only.
    """

    daily_puzzle_id: uuid.UUID
    played: bool
    result: MyResultPublic | None = None


class UpcomingEntryPublic(APIModel):
    scheduled_for: date
    difficulty: PuzzleDifficulty


class UpcomingListPublic(BaseModel):
    entries: list[UpcomingEntryPublic]


class GhostRankRequest(BaseModel):
    duration_ms: int = Field(ge=0)
    mistakes: int = Field(ge=0, le=3)


class GhostRankPublic(BaseModel):
    daily_puzzle_id: uuid.UUID
    duration_ms: int
    mistakes: int
    ghost_rank: int | None
    cohort_size: int
    percentile: float | None
    is_official: bool = False


# ---- Epic 6 — Social & Challenges ---------------------------------------


class UserSearchResultPublic(APIModel):
    id: uuid.UUID
    username: str | None
    display_name: str | None
    avatar_url: str | None
    relationship: str  # "self" | "friends" | "request_sent" | "request_received" | "none"


class UserSearchResponsePublic(BaseModel):
    results: list[UserSearchResultPublic]


class FriendPublic(APIModel):
    user_id: uuid.UUID
    username: str | None
    display_name: str | None
    avatar_url: str | None
    friend_since: datetime


class FriendsListPublic(BaseModel):
    friends: list[FriendPublic]


class FriendRequestPublic(APIModel):
    id: uuid.UUID
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    from_username: str | None
    from_display_name: str | None
    to_username: str | None
    to_display_name: str | None
    status: str
    created_at: datetime
    responded_at: datetime | None


class FriendRequestListPublic(BaseModel):
    incoming: list[FriendRequestPublic]
    outgoing: list[FriendRequestPublic]


class CreateFriendRequestBody(BaseModel):
    username: str = Field(min_length=1, max_length=32)


class ChallengeCreateRequest(BaseModel):
    daily_puzzle_id: uuid.UUID | None = None


class ChallengePublic(APIModel):
    id: uuid.UUID
    code: str
    daily_puzzle_id: uuid.UUID
    challenger_user_id: uuid.UUID
    challenger_username: str | None
    challenger_display_name: str | None
    challenger_duration_ms: int | None
    challenger_mistakes: int | None
    status: str
    created_at: datetime
    expires_at: datetime | None
    share_url: str


class ChallengeAcceptancePublic(APIModel):
    id: uuid.UUID
    challenge_id: uuid.UUID
    recipient_user_id: uuid.UUID | None
    recipient_username: str | None
    recipient_display_name: str | None
    duration_ms: int | None
    mistakes: int | None
    completed_at: datetime | None


class ChallengeDetailPublic(BaseModel):
    challenge: ChallengePublic
    acceptances: list[ChallengeAcceptancePublic]
    daily_difficulty: PuzzleDifficulty
    daily_scheduled_for: date


class MyChallengesPublic(BaseModel):
    sent: list[ChallengePublic]
    received: list[ChallengePublic]
