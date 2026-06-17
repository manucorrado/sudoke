"""Leaderboard + per-user result endpoints (PRD §15, §28.4)."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.principal import Principal, require_principal, require_user
from src.models import User
from src.schemas.common import (
    LeaderboardResponsePublic,
    LeaderboardRowPublic,
    MyResultPublic,
    RatingHistoryEntry,
    RatingHistoryResponse,
    RatingPublic,
)
from src.services.leaderboards import (
    LeaderboardView,
    get_leaderboard,
    get_my_result,
)
from src.services.rating import (
    PROVISIONAL_THRESHOLD,
    get_user_history,
    get_user_rating,
    tier_for_rating,
)

router = APIRouter(prefix="/daily", tags=["leaderboards"])


async def _get_daily_or_404(session: AsyncSession, daily_id: uuid.UUID):
    from src.models import DailyPuzzle

    daily = await session.get(DailyPuzzle, daily_id)
    if daily is None:
        raise HTTPException(status_code=404, detail="Daily puzzle not found")
    return daily


@router.get(
    "/{daily_puzzle_id}/leaderboard", response_model=LeaderboardResponsePublic
)
async def daily_leaderboard(
    daily_puzzle_id: uuid.UUID,
    view: Literal["global", "nearby", "friends", "historical"] = Query("global"),
    limit: int = Query(25, ge=1, le=100),
    principal: Principal = Depends(require_principal),
    session: AsyncSession = Depends(get_db),
) -> LeaderboardResponsePublic:
    daily = await _get_daily_or_404(session, daily_puzzle_id)

    # Guests can read global/historical boards but cannot get a personalized
    # nearby/friends view — fall back to global.
    me = principal.user
    effective_view: LeaderboardView = view
    if effective_view in {"nearby", "friends"} and me is None:
        effective_view = "global"

    payload = await get_leaderboard(
        session, daily, view=effective_view, limit=limit, me=me
    )
    return LeaderboardResponsePublic(
        daily_puzzle_id=payload.daily_puzzle_id,
        view=payload.view,
        cohort_size=payload.cohort_size,
        is_final=payload.is_final,
        rows=[
            LeaderboardRowPublic(
                rank=row.rank,
                user_id=row.user_id,
                username=row.username,
                display_name=row.display_name,
                avatar_url=row.avatar_url,
                official_duration_ms=row.official_duration_ms,
                mistakes=row.mistakes,
                rating=row.rating,
                rating_delta=row.rating_delta,
                tier=row.tier,
                is_me=row.is_me,
            )
            for row in payload.rows
        ],
    )


@router.get("/{daily_puzzle_id}/my-result", response_model=MyResultPublic)
async def daily_my_result(
    daily_puzzle_id: uuid.UUID,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> MyResultPublic:
    daily = await _get_daily_or_404(session, daily_puzzle_id)
    result = await get_my_result(session, daily, user)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attempt for this daily",
        )
    return MyResultPublic(
        daily_puzzle_id=daily.id,
        attempt_id=result.attempt_id,
        status=result.status,
        rank=result.rank,
        cohort_size=result.cohort_size,
        percentile=result.percentile,
        mistakes=result.mistakes,
        official_duration_ms=result.official_duration_ms,
        rating_before=result.rating_before,
        rating_after=result.rating_after,
        rating_delta=result.rating_delta,
        was_provisional=result.was_provisional,
        tier=result.tier,
        is_final=result.is_final,
    )


rating_router = APIRouter(prefix="/me", tags=["rating"])


@rating_router.get("/rating", response_model=RatingPublic)
async def my_rating(
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> RatingPublic:
    rating = await get_user_rating(session, user)
    return RatingPublic(
        rating=rating.rating,
        tier=tier_for_rating(rating.rating),
        provisional_completions=rating.provisional_completions,
        is_provisional=rating.provisional_completions < PROVISIONAL_THRESHOLD,
        calculation_version=rating.last_calculation_version,
        last_updated_at=rating.last_updated_at,
    )


@rating_router.get("/rating/history", response_model=RatingHistoryResponse)
async def my_rating_history(
    limit: int = Query(30, ge=1, le=100),
    kind: Literal["projected", "final"] | None = Query(default=None),
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> RatingHistoryResponse:
    entries = await get_user_history(session, user.id, limit=limit, kind=kind)
    return RatingHistoryResponse(
        entries=[
            RatingHistoryEntry(
                daily_puzzle_id=row.daily_puzzle_id,
                attempt_id=row.attempt_id,
                kind=row.kind,
                old_rating=row.old_rating,
                new_rating=row.new_rating,
                delta=row.delta,
                percentile=(
                    float(row.percentile) if row.percentile is not None else None
                ),
                cohort_size=row.cohort_size,
                was_provisional=row.was_provisional,
                calculation_version=row.calculation_version,
                applied_at=row.applied_at,
            )
            for row in entries
        ]
    )
