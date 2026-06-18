from __future__ import annotations

import uuid
from datetime import date, datetime

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
