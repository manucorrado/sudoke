"""Daily puzzle + ranked attempt endpoints (§28.2, §28.3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.principal import Principal, get_principal, require_principal
from src.models import RankedAttempt
from src.schemas.common import (
    AttemptEventBatch,
    AttemptEventResponse,
    AttemptResponse,
    DailyPuzzlePublic,
    SubmitAttemptRequest,
)
from src.services.attempts import (
    AttemptError,
    abandon_attempt,
    get_attempt,
    preview_attempt,
    record_events,
    start_attempt,
    submit_attempt,
)
from src.services.puzzles import get_active_daily_puzzle

router = APIRouter(prefix="/daily", tags=["daily"])


@router.get("/current", response_model=DailyPuzzlePublic)
async def current_daily_puzzle(
    session: AsyncSession = Depends(get_db),
) -> DailyPuzzlePublic:
    daily = await get_active_daily_puzzle(session)
    if daily is None or daily.puzzle is None:
        raise HTTPException(status_code=404, detail="No daily puzzle scheduled")
    puzzle = daily.puzzle
    return DailyPuzzlePublic(
        id=daily.id,
        scheduled_for=daily.scheduled_for,
        activate_at=daily.activate_at,
        finalize_at=daily.finalize_at,
        difficulty=puzzle.difficulty,
        estimated_min_seconds=puzzle.estimated_min_seconds,
        estimated_max_seconds=puzzle.estimated_max_seconds,
        givens=puzzle.givens,
    )


def _attempt_http(exc: AttemptError) -> HTTPException:
    return HTTPException(
        status_code=exc.http_status,
        detail={"code": exc.code, "message": exc.message},
    )


async def _get_daily_or_404(session: AsyncSession, daily_id: uuid.UUID):
    from src.models import DailyPuzzle  # local to avoid cycle in admin paths

    daily = await session.get(DailyPuzzle, daily_id)
    if daily is None:
        raise HTTPException(status_code=404, detail="Daily puzzle not found")
    return daily


@router.post("/{daily_puzzle_id}/preview", response_model=AttemptResponse)
async def preview(
    daily_puzzle_id: uuid.UUID,
    principal: Principal = Depends(require_principal),
    session: AsyncSession = Depends(get_db),
) -> RankedAttempt:
    daily = await _get_daily_or_404(session, daily_puzzle_id)
    try:
        return await preview_attempt(
            session, daily, user=principal.user, guest=principal.guest
        )
    except AttemptError as exc:
        raise _attempt_http(exc) from exc


@router.post("/{daily_puzzle_id}/start", response_model=AttemptResponse)
async def start(
    daily_puzzle_id: uuid.UUID,
    principal: Principal = Depends(require_principal),
    session: AsyncSession = Depends(get_db),
) -> RankedAttempt:
    daily = await _get_daily_or_404(session, daily_puzzle_id)
    try:
        return await start_attempt(
            session, daily, user=principal.user, guest=principal.guest
        )
    except AttemptError as exc:
        raise _attempt_http(exc) from exc


attempt_router = APIRouter(prefix="/ranked-attempts", tags=["ranked-attempts"])


async def _get_owned_attempt(
    session: AsyncSession, attempt_id: uuid.UUID, principal: Principal
) -> RankedAttempt:
    attempt = await get_attempt(session, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    is_owner = (
        principal.user is not None and attempt.user_id == principal.user.id
    ) or (
        principal.guest is not None and attempt.guest_session_id == principal.guest.id
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your attempt"
        )
    return attempt


@attempt_router.get("/{attempt_id}", response_model=AttemptResponse)
async def get_attempt_endpoint(
    attempt_id: uuid.UUID,
    principal: Principal = Depends(require_principal),
    session: AsyncSession = Depends(get_db),
) -> RankedAttempt:
    return await _get_owned_attempt(session, attempt_id, principal)


@attempt_router.post(
    "/{attempt_id}/events", response_model=list[AttemptEventResponse]
)
async def post_events(
    attempt_id: uuid.UUID,
    batch: AttemptEventBatch,
    principal: Principal = Depends(require_principal),
    session: AsyncSession = Depends(get_db),
):
    attempt = await _get_owned_attempt(session, attempt_id, principal)
    try:
        events = await record_events(session, attempt, batch.events)
    except AttemptError as exc:
        raise _attempt_http(exc) from exc
    return events


@attempt_router.post("/{attempt_id}/submit", response_model=AttemptResponse)
async def submit(
    attempt_id: uuid.UUID,
    payload: SubmitAttemptRequest,
    principal: Principal = Depends(require_principal),
    session: AsyncSession = Depends(get_db),
) -> RankedAttempt:
    attempt = await _get_owned_attempt(session, attempt_id, principal)
    daily = await _get_daily_or_404(session, attempt.daily_puzzle_id)
    if daily.puzzle is None:
        raise HTTPException(status_code=500, detail="Daily puzzle missing puzzle ref")
    try:
        return await submit_attempt(session, attempt, daily, daily.puzzle, payload)
    except AttemptError as exc:
        raise _attempt_http(exc) from exc


@attempt_router.post("/{attempt_id}/abandon", response_model=AttemptResponse)
async def abandon(
    attempt_id: uuid.UUID,
    principal: Principal = Depends(require_principal),
    session: AsyncSession = Depends(get_db),
) -> RankedAttempt:
    attempt = await _get_owned_attempt(session, attempt_id, principal)
    try:
        return await abandon_attempt(session, attempt)
    except AttemptError as exc:
        raise _attempt_http(exc) from exc
