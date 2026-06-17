"""Admin-only puzzle ops endpoints (§28.10)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.principal import require_admin
from src.models import DailyPuzzle, Puzzle, PuzzleStatus, User
from src.schemas.common import (
    BulkScheduleRequest,
    DailyPuzzleAdminResponse,
    PlaytestRequest,
    PuzzleAdminBulkImport,
    PuzzleAdminCreate,
    PuzzleAdminResponse,
    PuzzleReviewRequest,
)
from src.services.puzzles import (
    PuzzleImportError,
    approve_puzzle,
    import_puzzle,
    record_playtest,
    reject_puzzle,
    schedule_puzzles,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _import_error(exc: PuzzleImportError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"detail": "Puzzle validation failed", "issues": exc.issues},
    )


@router.post("/puzzles/import", response_model=list[PuzzleAdminResponse])
async def import_puzzles(
    payload: PuzzleAdminBulkImport | PuzzleAdminCreate,
    actor: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> list[Puzzle]:
    payloads: list[PuzzleAdminCreate]
    if isinstance(payload, PuzzleAdminBulkImport):
        payloads = payload.puzzles
    else:
        payloads = [payload]
    created: list[Puzzle] = []
    for spec in payloads:
        try:
            puzzle = await import_puzzle(session, spec, actor=actor)
        except PuzzleImportError as exc:
            raise _import_error(exc) from exc
        created.append(puzzle)
    return created


@router.get("/puzzles", response_model=list[PuzzleAdminResponse])
async def list_puzzles(
    status_filter: PuzzleStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> list[Puzzle]:
    stmt = select(Puzzle).order_by(Puzzle.created_at.desc()).limit(limit).offset(offset)
    if status_filter is not None:
        stmt = stmt.where(Puzzle.status == status_filter)
    result = await session.execute(stmt)
    return list(result.scalars())


@router.get("/puzzles/{puzzle_id}", response_model=PuzzleAdminResponse)
async def get_puzzle(
    puzzle_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> Puzzle:
    puzzle = await session.get(Puzzle, puzzle_id)
    if puzzle is None:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    return puzzle


@router.post(
    "/puzzles/{puzzle_id}/playtest",
    status_code=204,
)
async def playtest_puzzle(
    puzzle_id: uuid.UUID,
    payload: PlaytestRequest,
    actor: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> None:
    puzzle = await session.get(Puzzle, puzzle_id)
    if puzzle is None:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    await record_playtest(session, puzzle, actor=actor, payload=payload)


@router.post("/puzzles/{puzzle_id}/approve", response_model=PuzzleAdminResponse)
async def approve(
    puzzle_id: uuid.UUID,
    payload: PuzzleReviewRequest,
    actor: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> Puzzle:
    puzzle = await session.get(Puzzle, puzzle_id)
    if puzzle is None:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    try:
        return await approve_puzzle(
            session, puzzle, actor=actor, notes=payload.review_notes
        )
    except PuzzleImportError as exc:
        raise _import_error(exc) from exc


@router.post("/puzzles/{puzzle_id}/reject", response_model=PuzzleAdminResponse)
async def reject(
    puzzle_id: uuid.UUID,
    payload: PuzzleReviewRequest,
    actor: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> Puzzle:
    puzzle = await session.get(Puzzle, puzzle_id)
    if puzzle is None:
        raise HTTPException(status_code=404, detail="Puzzle not found")
    return await reject_puzzle(session, puzzle, actor=actor, notes=payload.review_notes)


@router.post(
    "/daily-puzzles/bulk-schedule", response_model=list[DailyPuzzleAdminResponse]
)
async def bulk_schedule(
    payload: BulkScheduleRequest,
    actor: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> list[DailyPuzzleAdminResponse]:
    try:
        scheduled = await schedule_puzzles(session, payload.entries, actor=actor)
    except PuzzleImportError as exc:
        raise _import_error(exc) from exc
    return [
        DailyPuzzleAdminResponse(
            id=daily.id,
            puzzle_id=daily.puzzle_id,
            scheduled_for=daily.scheduled_for,
            activate_at=daily.activate_at,
            finalize_at=daily.finalize_at,
            status=daily.status,
            difficulty=puzzle.difficulty,
        )
        for daily, puzzle in scheduled
    ]


@router.get("/daily-puzzles", response_model=list[DailyPuzzleAdminResponse])
async def list_daily_puzzles(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> list[DailyPuzzleAdminResponse]:
    stmt = (
        select(DailyPuzzle, Puzzle)
        .join(Puzzle, DailyPuzzle.puzzle_id == Puzzle.id)
        .order_by(DailyPuzzle.scheduled_for.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return [
        DailyPuzzleAdminResponse(
            id=daily.id,
            puzzle_id=daily.puzzle_id,
            scheduled_for=daily.scheduled_for,
            activate_at=daily.activate_at,
            finalize_at=daily.finalize_at,
            status=daily.status,
            difficulty=puzzle.difficulty,
        )
        for daily, puzzle in result.all()
    ]
