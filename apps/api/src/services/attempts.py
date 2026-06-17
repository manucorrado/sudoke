"""Server-authoritative ranked attempt lifecycle.

Implements PRD §25 (states), §26 (anti-cheat), and §8 (mistake counting).
The server owns timestamps; the client timer is decorative.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import sudoku
from src.models import (
    AttemptEventType,
    AttemptStatus,
    DailyPuzzle,
    GuestSession,
    Puzzle,
    RankedAttempt,
    RankedAttemptEvent,
    User,
)
from src.schemas.common import AttemptEventCreate, SubmitAttemptRequest
from src.services.rating import project_for_attempt


class AttemptError(Exception):
    """User-actionable failure during an attempt."""

    def __init__(self, code: str, message: str, http_status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


async def get_attempt(session: AsyncSession, attempt_id: uuid.UUID) -> RankedAttempt | None:
    result = await session.execute(
        select(RankedAttempt).where(RankedAttempt.id == attempt_id)
    )
    return result.scalar_one_or_none()


async def get_existing_attempt(
    session: AsyncSession,
    *,
    daily_puzzle_id: uuid.UUID,
    user: User | None,
    guest: GuestSession | None,
) -> RankedAttempt | None:
    stmt = select(RankedAttempt).where(RankedAttempt.daily_puzzle_id == daily_puzzle_id)
    if user is not None:
        stmt = stmt.where(RankedAttempt.user_id == user.id)
    elif guest is not None:
        stmt = stmt.where(RankedAttempt.guest_session_id == guest.id)
    else:
        raise AttemptError("auth_required", "Authentication required", http_status=401)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def preview_attempt(
    session: AsyncSession,
    daily: DailyPuzzle,
    *,
    user: User | None,
    guest: GuestSession | None,
    now: datetime | None = None,
) -> RankedAttempt:
    """Begin a preview. Does **not** consume the attempt."""

    if daily.finalize_at <= (now or datetime.now(timezone.utc)):
        raise AttemptError("daily_closed", "Daily puzzle is closed", http_status=409)
    existing = await get_existing_attempt(
        session, daily_puzzle_id=daily.id, user=user, guest=guest
    )
    if existing is not None:
        if existing.status not in {AttemptStatus.not_started, AttemptStatus.previewing}:
            raise AttemptError(
                "attempt_consumed",
                "Attempt already started or consumed for this daily puzzle",
                http_status=409,
            )
        existing.status = AttemptStatus.previewing
        existing.previewed_at = now or datetime.now(timezone.utc)
        await _add_event(
            session,
            existing,
            AttemptEventType.preview_started,
            payload=None,
            occurred_at=existing.previewed_at,
        )
        return existing

    attempt = RankedAttempt(
        user_id=user.id if user else None,
        guest_session_id=guest.id if guest else None,
        daily_puzzle_id=daily.id,
        status=AttemptStatus.previewing,
        previewed_at=now or datetime.now(timezone.utc),
        mistakes=0,
    )
    session.add(attempt)
    await session.flush()
    await _add_event(
        session,
        attempt,
        AttemptEventType.preview_started,
        payload=None,
        occurred_at=attempt.previewed_at or datetime.now(timezone.utc),
    )
    return attempt


async def start_attempt(
    session: AsyncSession,
    daily: DailyPuzzle,
    *,
    user: User | None,
    guest: GuestSession | None,
    now: datetime | None = None,
) -> RankedAttempt:
    """Transition into `started`. **Consumes the attempt.**"""

    moment = now or datetime.now(timezone.utc)
    if daily.finalize_at <= moment:
        raise AttemptError("daily_closed", "Daily puzzle is closed", http_status=409)
    attempt = await get_existing_attempt(
        session, daily_puzzle_id=daily.id, user=user, guest=guest
    )
    if attempt is None:
        attempt = RankedAttempt(
            user_id=user.id if user else None,
            guest_session_id=guest.id if guest else None,
            daily_puzzle_id=daily.id,
            status=AttemptStatus.not_started,
        )
        session.add(attempt)
    if attempt.status not in {
        AttemptStatus.not_started,
        AttemptStatus.previewing,
    }:
        raise AttemptError(
            "attempt_consumed",
            "Attempt already started or consumed for this daily puzzle",
            http_status=409,
        )
    attempt.status = AttemptStatus.started
    attempt.started_at = moment
    await session.flush()
    await _add_event(
        session, attempt, AttemptEventType.started, payload=None, occurred_at=moment
    )
    attempt.status = AttemptStatus.in_progress
    return attempt


async def abandon_attempt(
    session: AsyncSession,
    attempt: RankedAttempt,
    *,
    now: datetime | None = None,
) -> RankedAttempt:
    if attempt.status in {
        AttemptStatus.submitted,
        AttemptStatus.validated,
        AttemptStatus.finalized,
    }:
        raise AttemptError("invalid_state", "Attempt already submitted")
    moment = now or datetime.now(timezone.utc)
    attempt.status = AttemptStatus.abandoned
    attempt.abandoned_at = moment
    await _add_event(
        session,
        attempt,
        AttemptEventType.abandoned,
        payload=None,
        occurred_at=moment,
    )
    return attempt


async def record_events(
    session: AsyncSession,
    attempt: RankedAttempt,
    events: list[AttemptEventCreate],
) -> list[RankedAttemptEvent]:
    if attempt.status not in {AttemptStatus.in_progress, AttemptStatus.started}:
        raise AttemptError("invalid_state", "Attempt not in progress")
    moment = datetime.now(timezone.utc)
    persisted: list[RankedAttemptEvent] = []
    for ev in events:
        persisted.append(
            await _add_event(
                session,
                attempt,
                ev.event_type,
                payload=ev.payload,
                occurred_at=moment,
                client_ts=ev.client_ts,
            )
        )
    return persisted


async def submit_attempt(
    session: AsyncSession,
    attempt: RankedAttempt,
    daily: DailyPuzzle,
    puzzle: Puzzle,
    payload: SubmitAttemptRequest,
    *,
    now: datetime | None = None,
) -> RankedAttempt:
    """Submit the final grid, validate it, and mark provisional_ranked."""

    moment = now or datetime.now(timezone.utc)
    if attempt.status not in {
        AttemptStatus.started,
        AttemptStatus.in_progress,
    }:
        raise AttemptError("invalid_state", "Attempt not in progress")
    if daily.finalize_at <= moment:
        raise AttemptError("daily_closed", "Daily puzzle is closed", http_status=409)

    submitted_grid = sudoku.parse_grid(payload.submitted_grid)
    solution_grid = sudoku.parse_grid(puzzle.solution)
    result = sudoku.validate_submission(submitted_grid, solution_grid)

    if not result.valid:
        raise AttemptError(
            "submission_invalid",
            f"Submission has {result.mistakes} wrong cells; cannot accept",
        )

    if attempt.started_at is None:
        raise AttemptError("invalid_state", "started_at missing")

    attempt.status = AttemptStatus.submitted
    attempt.submitted_at = moment
    attempt.mistakes = payload.mistakes
    attempt.submitted_grid = payload.submitted_grid
    attempt.official_duration_ms = int(
        (moment - attempt.started_at).total_seconds() * 1000
    )
    await _add_event(
        session,
        attempt,
        AttemptEventType.submitted,
        payload={"mistakes": payload.mistakes},
        occurred_at=moment,
    )

    # Anti-cheat: conservative absolute threshold per difficulty (§26.2).
    threshold = sudoku.SUSPICIOUS_SOLVE_THRESHOLDS_SECONDS[puzzle.difficulty.value]
    if attempt.official_duration_ms < threshold * 1000:
        attempt.status = AttemptStatus.under_review
        attempt.under_review_reason = "fast_solve_threshold"
        await _add_event(
            session,
            attempt,
            AttemptEventType.under_review,
            payload={"reason": attempt.under_review_reason},
            occurred_at=moment,
        )
        return attempt

    attempt.status = AttemptStatus.validated
    attempt.validated_at = moment
    await _add_event(
        session,
        attempt,
        AttemptEventType.validated,
        payload=None,
        occurred_at=moment,
    )
    attempt.status = AttemptStatus.provisional_ranked

    if attempt.user_id is not None:
        await project_for_attempt(
            session, attempt=attempt, puzzle_difficulty=puzzle.difficulty
        )
    return attempt


async def timeout_due_attempts(
    session: AsyncSession, *, now: datetime | None = None
) -> list[uuid.UUID]:
    """Time out any in-progress attempts whose daily window has closed."""

    moment = now or datetime.now(timezone.utc)
    result = await session.execute(
        select(RankedAttempt)
        .join(DailyPuzzle, RankedAttempt.daily_puzzle_id == DailyPuzzle.id)
        .where(DailyPuzzle.finalize_at <= moment)
        .where(
            RankedAttempt.status.in_(
                (
                    AttemptStatus.previewing,
                    AttemptStatus.started,
                    AttemptStatus.in_progress,
                )
            )
        )
    )
    timed_out: list[uuid.UUID] = []
    for attempt in result.scalars():
        attempt.status = AttemptStatus.timed_out
        attempt.timed_out_at = moment
        timed_out.append(attempt.id)
        await _add_event(
            session,
            attempt,
            AttemptEventType.timed_out,
            payload=None,
            occurred_at=moment,
        )
    return timed_out


async def _add_event(
    session: AsyncSession,
    attempt: RankedAttempt,
    event_type: AttemptEventType,
    *,
    payload: dict | None,
    occurred_at: datetime,
    client_ts: datetime | None = None,
) -> RankedAttemptEvent:
    event = RankedAttemptEvent(
        attempt_id=attempt.id,
        event_type=event_type,
        occurred_at=occurred_at,
        client_ts=client_ts,
        payload=payload,
    )
    session.add(event)
    return event
