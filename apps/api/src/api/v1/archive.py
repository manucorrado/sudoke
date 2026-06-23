"""Archive + ghost rank endpoints (PRD §12, Epic 7).

Endpoints (read-only / casual):

  - GET  /archive
  - GET  /archive/upcoming
  - GET  /archive/{daily_puzzle_id}
  - POST /archive/{daily_puzzle_id}/ghost-rank

No persistent attempt is created here — archive replays are practice
mode and never mutate rating or leaderboards.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.common import (
    ArchiveDetailPublic,
    ArchiveEntryPublic,
    ArchiveListPublic,
    GhostRankPublic,
    GhostRankRequest,
    UpcomingEntryPublic,
    UpcomingListPublic,
)
from src.services.archive import (
    compute_ghost_rank,
    get_archive_detail,
    list_archive,
    list_upcoming,
)

router = APIRouter(prefix="/archive", tags=["archive"])


@router.get("", response_model=ArchiveListPublic)
async def archive_list(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> ArchiveListPublic:
    entries = await list_archive(session, limit=limit, offset=offset)
    return ArchiveListPublic(
        entries=[ArchiveEntryPublic.model_validate(e) for e in entries]
    )


@router.get("/upcoming", response_model=UpcomingListPublic)
async def archive_upcoming(
    limit: int = Query(default=14, ge=1, le=60),
    session: AsyncSession = Depends(get_db),
) -> UpcomingListPublic:
    entries = await list_upcoming(session, limit=limit)
    return UpcomingListPublic(
        entries=[UpcomingEntryPublic.model_validate(e) for e in entries]
    )


@router.get("/{daily_puzzle_id}", response_model=ArchiveDetailPublic)
async def archive_detail(
    daily_puzzle_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ArchiveDetailPublic:
    detail = await get_archive_detail(session, daily_puzzle_id)
    if detail is None:
        raise HTTPException(
            status_code=404, detail="Archive puzzle not found or still open"
        )
    return ArchiveDetailPublic.model_validate(detail)


@router.post(
    "/{daily_puzzle_id}/ghost-rank",
    response_model=GhostRankPublic,
)
async def archive_ghost_rank(
    daily_puzzle_id: uuid.UUID,
    payload: GhostRankRequest,
    session: AsyncSession = Depends(get_db),
) -> GhostRankPublic:
    detail = await get_archive_detail(session, daily_puzzle_id)
    if detail is None:
        raise HTTPException(
            status_code=404, detail="Archive puzzle not found or still open"
        )
    ghost = await compute_ghost_rank(
        session,
        daily_puzzle_id,
        duration_ms=payload.duration_ms,
        mistakes=payload.mistakes,
    )
    assert ghost is not None  # detail guard returned 404 otherwise
    return GhostRankPublic(
        daily_puzzle_id=ghost.daily_puzzle_id,
        duration_ms=ghost.duration_ms,
        mistakes=ghost.mistakes,
        ghost_rank=ghost.ghost_rank,
        cohort_size=ghost.cohort_size,
        percentile=ghost.percentile,
    )
