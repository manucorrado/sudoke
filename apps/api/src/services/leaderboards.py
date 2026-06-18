"""Daily leaderboard queries (PRD §15, §28.4).

Three live views (global, nearby, friends-stub) plus a historical view
that reads from `DailyResult` once a daily is finalized.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    AttemptStatus,
    DailyPuzzle,
    DailyPuzzleStatus,
    DailyResult,
    RankedAttempt,
    RatingHistory,
    User,
    UserRating,
)
from src.services.rating import (
    RATING_ELIGIBLE_STATUSES,
    STARTING_RATING,
    tier_for_rating,
)

LeaderboardView = Literal["global", "nearby", "friends", "historical"]


@dataclass(frozen=True)
class LeaderboardRow:
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


@dataclass(frozen=True)
class LeaderboardResponse:
    view: LeaderboardView
    cohort_size: int
    rows: list[LeaderboardRow]
    is_final: bool
    daily_puzzle_id: uuid.UUID


def _row_from_live(
    *,
    rank: int,
    attempt: RankedAttempt,
    user: User,
    rating_value: int,
    rating_delta: int | None,
    is_me: bool,
) -> LeaderboardRow:
    return LeaderboardRow(
        rank=rank,
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        official_duration_ms=attempt.official_duration_ms or 0,
        mistakes=attempt.mistakes,
        rating=rating_value,
        rating_delta=rating_delta,
        tier=tier_for_rating(rating_value),
        is_me=is_me,
    )


def _row_from_final(
    *,
    rank: int,
    result: DailyResult,
    user: User,
    is_me: bool,
) -> LeaderboardRow:
    return LeaderboardRow(
        rank=rank,
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        official_duration_ms=result.official_duration_ms,
        mistakes=result.mistakes,
        rating=result.rating_after,
        rating_delta=result.rating_delta,
        tier=tier_for_rating(result.rating_after),
        is_me=is_me,
    )


async def _ordered_live_cohort(
    session: AsyncSession, daily_puzzle_id: uuid.UUID
) -> list[RankedAttempt]:
    stmt = (
        select(RankedAttempt)
        .where(RankedAttempt.daily_puzzle_id == daily_puzzle_id)
        .where(RankedAttempt.user_id.isnot(None))
        .where(RankedAttempt.official_duration_ms.isnot(None))
        .where(RankedAttempt.status.in_(tuple(RATING_ELIGIBLE_STATUSES)))
        .order_by(
            RankedAttempt.mistakes.asc(),
            RankedAttempt.official_duration_ms.asc(),
            RankedAttempt.submitted_at.asc(),
        )
    )
    return list((await session.execute(stmt)).scalars())


async def _ordered_final_cohort(
    session: AsyncSession, daily_puzzle_id: uuid.UUID
) -> list[DailyResult]:
    stmt = (
        select(DailyResult)
        .where(DailyResult.daily_puzzle_id == daily_puzzle_id)
        .order_by(DailyResult.rank.asc())
    )
    return list((await session.execute(stmt)).scalars())


async def _user_map(
    session: AsyncSession, user_ids: list[uuid.UUID]
) -> dict[uuid.UUID, User]:
    if not user_ids:
        return {}
    stmt = select(User).where(User.id.in_(user_ids))
    result = await session.execute(stmt)
    return {u.id: u for u in result.scalars()}


async def _rating_map(
    session: AsyncSession, user_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    if not user_ids:
        return {}
    stmt = select(UserRating).where(UserRating.user_id.in_(user_ids))
    result = await session.execute(stmt)
    return {r.user_id: r.rating for r in result.scalars()}


async def _projected_delta_map(
    session: AsyncSession,
    daily_puzzle_id: uuid.UUID,
    user_ids: list[uuid.UUID],
) -> dict[uuid.UUID, int]:
    if not user_ids:
        return {}
    stmt = (
        select(RatingHistory)
        .where(RatingHistory.daily_puzzle_id == daily_puzzle_id)
        .where(RatingHistory.user_id.in_(user_ids))
        .where(RatingHistory.kind == "projected")
    )
    result = await session.execute(stmt)
    return {r.user_id: r.delta for r in result.scalars()}


def _index_of(rows: list[RankedAttempt], user_id: uuid.UUID | None) -> int | None:
    if user_id is None:
        return None
    for idx, attempt in enumerate(rows):
        if attempt.user_id == user_id:
            return idx
    return None


async def get_leaderboard(
    session: AsyncSession,
    daily: DailyPuzzle,
    *,
    view: LeaderboardView = "global",
    limit: int = 25,
    me: User | None = None,
) -> LeaderboardResponse:
    """Return a leaderboard page for the requested view.

    `view="historical"` is the read-only snapshot built once daily closes.
    Live views (`global`, `nearby`, `friends`) work while the daily is open.
    `friends` currently returns rows from the global cohort restricted to
    the caller (Epic 6 will wire the actual friends graph).
    """

    is_final = daily.status == DailyPuzzleStatus.finalized

    if view == "historical" or is_final:
        final_rows = await _ordered_final_cohort(session, daily.id)
        users = await _user_map(session, [r.user_id for r in final_rows])
        rows: list[LeaderboardRow] = []
        my_index = (
            next(
                (i for i, r in enumerate(final_rows) if me and r.user_id == me.id),
                None,
            )
            if me
            else None
        )
        slice_start, slice_end = _slice_for(view, my_index, len(final_rows), limit)
        for offset, result in enumerate(final_rows[slice_start:slice_end]):
            user = users.get(result.user_id)
            if user is None:
                continue
            rows.append(
                _row_from_final(
                    rank=slice_start + offset + 1,
                    result=result,
                    user=user,
                    is_me=bool(me and me.id == result.user_id),
                )
            )
        return LeaderboardResponse(
            view="historical" if view == "historical" or is_final else view,
            cohort_size=len(final_rows),
            rows=rows,
            is_final=True,
            daily_puzzle_id=daily.id,
        )

    cohort = await _ordered_live_cohort(session, daily.id)
    user_ids = [a.user_id for a in cohort if a.user_id is not None]
    users = await _user_map(session, user_ids)
    ratings = await _rating_map(session, user_ids)
    projected = await _projected_delta_map(session, daily.id, user_ids)

    my_index = _index_of(cohort, me.id if me else None)
    if view == "friends":
        # Friends graph not yet implemented (Epic 6). Return just the caller.
        filtered = [(i, a) for i, a in enumerate(cohort) if me and a.user_id == me.id]
        slice_view = filtered[:limit]
    else:
        slice_start, slice_end = _slice_for(view, my_index, len(cohort), limit)
        slice_view = list(enumerate(cohort))[slice_start:slice_end]

    rows = []
    for idx, attempt in slice_view:
        if attempt.user_id is None:
            continue
        user = users.get(attempt.user_id)
        if user is None:
            continue
        rows.append(
            _row_from_live(
                rank=idx + 1,
                attempt=attempt,
                user=user,
                rating_value=ratings.get(attempt.user_id, STARTING_RATING),
                rating_delta=projected.get(attempt.user_id),
                is_me=bool(me and me.id == attempt.user_id),
            )
        )
    return LeaderboardResponse(
        view=view,
        cohort_size=len(cohort),
        rows=rows,
        is_final=False,
        daily_puzzle_id=daily.id,
    )


def _slice_for(
    view: LeaderboardView,
    my_index: int | None,
    cohort_size: int,
    limit: int,
) -> tuple[int, int]:
    """Return (start, end) indices for a paginated view.

    `global` and `historical` show the top `limit` rows; `nearby` centers
    the window on the caller. `nearby` falls back to top-of-board when the
    caller has no eligible attempt.
    """

    if view == "nearby" and my_index is not None:
        half = max(1, limit // 2)
        start = max(0, my_index - half)
        end = min(cohort_size, start + limit)
        # If we hit the bottom, pull start up.
        if end - start < limit:
            start = max(0, end - limit)
        return start, end
    return 0, min(limit, cohort_size)


@dataclass(frozen=True)
class MyResult:
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


async def get_my_result(
    session: AsyncSession,
    daily: DailyPuzzle,
    user: User,
) -> MyResult | None:
    """Return my row on the leaderboard for this daily (or None if none)."""

    stmt = (
        select(RankedAttempt)
        .where(RankedAttempt.daily_puzzle_id == daily.id)
        .where(RankedAttempt.user_id == user.id)
    )
    attempt = (await session.execute(stmt)).scalar_one_or_none()
    if attempt is None:
        return None

    if daily.status == DailyPuzzleStatus.finalized:
        final_stmt = (
            select(DailyResult)
            .where(DailyResult.daily_puzzle_id == daily.id)
            .where(DailyResult.user_id == user.id)
        )
        final = (await session.execute(final_stmt)).scalar_one_or_none()
        if final is not None:
            return MyResult(
                attempt_id=attempt.id,
                status=attempt.status,
                rank=final.rank,
                cohort_size=final.cohort_size,
                percentile=float(final.percentile),
                mistakes=final.mistakes,
                official_duration_ms=final.official_duration_ms,
                rating_before=final.rating_before,
                rating_after=final.rating_after,
                rating_delta=final.rating_delta,
                was_provisional=final.was_provisional,
                tier=tier_for_rating(final.rating_after),
                is_final=True,
            )

    # Live view: compute rank within current cohort + read projected row.
    cohort = await _ordered_live_cohort(session, daily.id)
    rank = None
    for i, a in enumerate(cohort):
        if a.id == attempt.id:
            rank = i + 1
            break

    proj_stmt = (
        select(RatingHistory)
        .where(RatingHistory.daily_puzzle_id == daily.id)
        .where(RatingHistory.user_id == user.id)
        .where(RatingHistory.kind == "projected")
    )
    proj = (await session.execute(proj_stmt)).scalar_one_or_none()

    return MyResult(
        attempt_id=attempt.id,
        status=attempt.status,
        rank=rank,
        cohort_size=len(cohort),
        percentile=(
            float(proj.percentile)
            if proj and proj.percentile is not None
            else None
        ),
        mistakes=attempt.mistakes,
        official_duration_ms=attempt.official_duration_ms,
        rating_before=proj.old_rating if proj else None,
        rating_after=proj.new_rating if proj else None,
        rating_delta=proj.delta if proj else None,
        was_provisional=bool(proj.was_provisional) if proj else False,
        tier=tier_for_rating(proj.new_rating) if proj else None,
        is_final=False,
    )


__all__ = [
    "LeaderboardResponse",
    "LeaderboardRow",
    "LeaderboardView",
    "MyResult",
    "get_leaderboard",
    "get_my_result",
]
