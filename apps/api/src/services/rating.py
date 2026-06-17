"""Rating engine and finalization (PRD §14).

Two entry points:

- `project_rating_delta(...)` — pure, deterministic projection used to give
  the player immediate feedback after a valid submission. The projection
  assumes the current cohort snapshot at submit time; the final delta may
  differ once more players complete.

- `finalize_daily_ratings(...)` — recomputes percentiles for the entire
  validated cohort after the daily window closes, writes a `final` row
  to `rating_history`, updates `UserRating`, and snapshots a `DailyResult`
  per finalist. Idempotent: running twice for the same daily is a no-op
  (guarded by `UserRating.last_finalized_daily_id`).
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    AttemptStatus,
    DailyPuzzle,
    DailyResult,
    RankedAttempt,
    RatingHistory,
    User,
    UserRating,
)
from src.models.puzzles import PuzzleDifficulty

CALCULATION_VERSION = "v1"

STARTING_RATING = 1000
RATING_FLOOR = 100
PROVISIONAL_THRESHOLD = 10
PROVISIONAL_CAP = 80
NORMAL_CAP = 35

# §14.8 — difficulty multipliers. Expert is not part of the MVP ranked
# rotation but we keep a multiplier so we never accidentally divide by zero.
DIFFICULTY_MULTIPLIERS: dict[PuzzleDifficulty, float] = {
    PuzzleDifficulty.easy: 0.85,
    PuzzleDifficulty.medium: 1.0,
    PuzzleDifficulty.hard: 1.1,
    PuzzleDifficulty.expert: 1.0,
}

# Statuses that count toward the rating cohort (§14.3).
RATING_ELIGIBLE_STATUSES: frozenset[AttemptStatus] = frozenset(
    {AttemptStatus.provisional_ranked, AttemptStatus.validated, AttemptStatus.finalized}
)


def _cohort_dampening(cohort_size: int) -> float:
    """Small-cohort dampening (§14.9)."""

    if cohort_size < 10:
        return 0.0
    if cohort_size < 50:
        return 0.4
    return 1.0


def tier_for_rating(rating: int) -> str:
    """Cosmetic tier band — §14.12."""

    if rating < 800:
        return "bronze"
    if rating < 1000:
        return "silver"
    if rating < 1200:
        return "gold"
    if rating < 1500:
        return "platinum"
    if rating < 1800:
        return "diamond"
    return "master"


@dataclass(frozen=True)
class RatingProjection:
    old_rating: int
    new_rating: int
    delta: int
    percentile: float
    cohort_size: int
    is_provisional: bool
    calculation_version: str
    tier: str


def compute_delta(
    *,
    current_rating: int,
    percentile: float,
    difficulty: PuzzleDifficulty,
    cohort_size: int,
    is_provisional: bool,
) -> int:
    """Compute a single integer rating delta.

    Performance is mapped from percentile (0..100 where higher = better) onto
    a symmetric -1..1 score, scaled by difficulty multiplier, cap, and the
    small-cohort dampening factor. The 50th percentile = no change.
    """

    if cohort_size < 1:
        return 0
    multiplier = DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)
    cap = PROVISIONAL_CAP if is_provisional else NORMAL_CAP
    performance_score = (percentile - 50.0) / 50.0  # range -1..1
    dampened = performance_score * _cohort_dampening(cohort_size)
    raw = dampened * cap * multiplier
    # Bias rounding away from zero so a 50.5 percentile still nudges +1.
    delta = int(math.copysign(math.floor(abs(raw) + 0.5), raw))
    return max(-cap, min(cap, delta))


def apply_rating_change(current_rating: int, delta: int) -> int:
    """Clamp the new rating to the floor."""

    return max(RATING_FLOOR, current_rating + delta)


async def get_or_create_rating(
    session: AsyncSession, user_id: uuid.UUID
) -> UserRating:
    result = await session.execute(
        select(UserRating).where(UserRating.user_id == user_id)
    )
    rating = result.scalar_one_or_none()
    if rating is None:
        rating = UserRating(
            user_id=user_id,
            rating=STARTING_RATING,
            provisional_completions=0,
            last_calculation_version=CALCULATION_VERSION,
        )
        session.add(rating)
        await session.flush()
    return rating


async def _cohort_for_daily(
    session: AsyncSession, daily_puzzle_id: uuid.UUID
) -> list[RankedAttempt]:
    """Return rating-eligible attempts for a daily, fastest-first.

    Excludes guest attempts (no rating without an account) and excludes
    statuses outside `RATING_ELIGIBLE_STATUSES`.
    """

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
    result = await session.execute(stmt)
    return list(result.scalars())


def _percentile_for_rank(rank: int, cohort_size: int) -> float:
    """Percentile (0..100, higher = better) for a 1-indexed rank.

    With one player, that player is treated as the 50th percentile so
    their rating is unaffected.
    """

    if cohort_size <= 1:
        return 50.0
    # Standard "percent of players you finished ahead of" — fastest player
    # has rank 1 and a percentile of (cohort_size - 1) / cohort_size * 100.
    return (cohort_size - rank) / (cohort_size - 1) * 100.0


def _percentile_for_attempt(
    cohort: list[RankedAttempt], attempt: RankedAttempt
) -> tuple[float, int]:
    """Return (percentile, rank) for an attempt within an ordered cohort."""

    for idx, candidate in enumerate(cohort):
        if candidate.id == attempt.id:
            rank = idx + 1
            return _percentile_for_rank(rank, len(cohort)), rank
    return 50.0, len(cohort) + 1


async def project_for_attempt(
    session: AsyncSession,
    *,
    attempt: RankedAttempt,
    puzzle_difficulty: PuzzleDifficulty,
) -> RatingProjection | None:
    """Compute the immediate projected rating change for a single attempt.

    Returns None for guest attempts (no account = no rating).
    Writes a `RatingHistory` row with `kind="projected"` so the Profile
    history shows the impact even before finalization. The user's
    `UserRating` row is NOT updated until finalize.
    """

    if attempt.user_id is None or attempt.official_duration_ms is None:
        return None

    # Include the just-submitted attempt in the cohort snapshot.
    cohort = await _cohort_for_daily(session, attempt.daily_puzzle_id)
    if not any(a.id == attempt.id for a in cohort):
        cohort.append(attempt)
        cohort.sort(
            key=lambda a: (
                a.mistakes,
                a.official_duration_ms or 0,
                a.submitted_at or datetime.now(timezone.utc),
            )
        )
    percentile, _rank = _percentile_for_attempt(cohort, attempt)

    rating = await get_or_create_rating(session, attempt.user_id)
    is_provisional = rating.provisional_completions < PROVISIONAL_THRESHOLD
    delta = compute_delta(
        current_rating=rating.rating,
        percentile=percentile,
        difficulty=puzzle_difficulty,
        cohort_size=len(cohort),
        is_provisional=is_provisional,
    )
    new_rating = apply_rating_change(rating.rating, delta)

    # Replace any prior projected row for this attempt (idempotent re-submits).
    await _upsert_history(
        session,
        user_id=attempt.user_id,
        daily_puzzle_id=attempt.daily_puzzle_id,
        attempt_id=attempt.id,
        kind="projected",
        old_rating=rating.rating,
        new_rating=new_rating,
        delta=delta,
        percentile=percentile,
        cohort_size=len(cohort),
        was_provisional=is_provisional,
    )
    attempt.calculation_version = CALCULATION_VERSION

    return RatingProjection(
        old_rating=rating.rating,
        new_rating=new_rating,
        delta=delta,
        percentile=percentile,
        cohort_size=len(cohort),
        is_provisional=is_provisional,
        calculation_version=CALCULATION_VERSION,
        tier=tier_for_rating(new_rating),
    )


async def _upsert_history(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    daily_puzzle_id: uuid.UUID,
    attempt_id: uuid.UUID,
    kind: str,
    old_rating: int,
    new_rating: int,
    delta: int,
    percentile: float,
    cohort_size: int,
    was_provisional: bool,
    applied_at: datetime | None = None,
) -> RatingHistory:
    moment = applied_at or datetime.now(timezone.utc)
    stmt = (
        select(RatingHistory)
        .where(RatingHistory.user_id == user_id)
        .where(RatingHistory.daily_puzzle_id == daily_puzzle_id)
        .where(RatingHistory.kind == kind)
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        existing.attempt_id = attempt_id
        existing.old_rating = old_rating
        existing.new_rating = new_rating
        existing.delta = delta
        existing.percentile = percentile
        existing.cohort_size = cohort_size
        existing.was_provisional = was_provisional
        existing.calculation_version = CALCULATION_VERSION
        existing.applied_at = moment
        return existing
    row = RatingHistory(
        user_id=user_id,
        daily_puzzle_id=daily_puzzle_id,
        attempt_id=attempt_id,
        kind=kind,
        old_rating=old_rating,
        new_rating=new_rating,
        delta=delta,
        percentile=percentile,
        cohort_size=cohort_size,
        was_provisional=was_provisional,
        calculation_version=CALCULATION_VERSION,
        applied_at=moment,
    )
    session.add(row)
    return row


@dataclass(frozen=True)
class FinalizedAttempt:
    user_id: uuid.UUID
    attempt_id: uuid.UUID
    rank: int
    percentile: float
    delta: int
    new_rating: int


async def finalize_daily_ratings(
    session: AsyncSession,
    daily: DailyPuzzle,
    *,
    now: datetime | None = None,
) -> list[FinalizedAttempt]:
    """Finalize ratings + leaderboard snapshot for a closed daily puzzle.

    Idempotent: subsequent calls return an empty list (results already
    written). Moves each rated attempt to `AttemptStatus.finalized`.
    """

    moment = now or datetime.now(timezone.utc)
    if daily.puzzle is None:
        return []
    difficulty = daily.puzzle.difficulty

    cohort = await _cohort_for_daily(session, daily.id)
    if not cohort:
        return []

    cohort_size = len(cohort)
    finalized: list[FinalizedAttempt] = []
    for idx, attempt in enumerate(cohort):
        if attempt.user_id is None or attempt.official_duration_ms is None:
            continue
        rank = idx + 1
        percentile = _percentile_for_rank(rank, cohort_size)

        rating = await get_or_create_rating(session, attempt.user_id)
        # Idempotency: if we've already finalized this user for this daily,
        # skip to avoid double-applying deltas.
        existing_result = await session.execute(
            select(DailyResult)
            .where(DailyResult.user_id == attempt.user_id)
            .where(DailyResult.daily_puzzle_id == daily.id)
        )
        if existing_result.scalar_one_or_none() is not None:
            attempt.status = AttemptStatus.finalized
            attempt.finalized_at = moment
            continue

        is_provisional = rating.provisional_completions < PROVISIONAL_THRESHOLD
        delta = compute_delta(
            current_rating=rating.rating,
            percentile=percentile,
            difficulty=difficulty,
            cohort_size=cohort_size,
            is_provisional=is_provisional,
        )
        old_rating = rating.rating
        new_rating = apply_rating_change(old_rating, delta)

        rating.rating = new_rating
        rating.provisional_completions += 1
        rating.last_calculation_version = CALCULATION_VERSION
        rating.last_finalized_daily_id = daily.id
        rating.last_updated_at = moment

        await _upsert_history(
            session,
            user_id=attempt.user_id,
            daily_puzzle_id=daily.id,
            attempt_id=attempt.id,
            kind="final",
            old_rating=old_rating,
            new_rating=new_rating,
            delta=delta,
            percentile=percentile,
            cohort_size=cohort_size,
            was_provisional=is_provisional,
            applied_at=moment,
        )

        session.add(
            DailyResult(
                user_id=attempt.user_id,
                daily_puzzle_id=daily.id,
                attempt_id=attempt.id,
                rank=rank,
                cohort_size=cohort_size,
                percentile=percentile,
                mistakes=attempt.mistakes,
                official_duration_ms=attempt.official_duration_ms,
                rating_before=old_rating,
                rating_after=new_rating,
                rating_delta=delta,
                was_provisional=is_provisional,
                calculation_version=CALCULATION_VERSION,
                finalized_at=moment,
            )
        )

        attempt.status = AttemptStatus.finalized
        attempt.finalized_at = moment

        finalized.append(
            FinalizedAttempt(
                user_id=attempt.user_id,
                attempt_id=attempt.id,
                rank=rank,
                percentile=percentile,
                delta=delta,
                new_rating=new_rating,
            )
        )
    return finalized


async def get_user_rating(
    session: AsyncSession, user: User
) -> UserRating:
    return await get_or_create_rating(session, user.id)


async def get_user_history(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    limit: int = 30,
    kind: str | None = None,
) -> list[RatingHistory]:
    stmt = (
        select(RatingHistory)
        .where(RatingHistory.user_id == user_id)
        .order_by(RatingHistory.applied_at.desc())
        .limit(limit)
    )
    if kind is not None:
        stmt = stmt.where(RatingHistory.kind == kind)
    result = await session.execute(stmt)
    return list(result.scalars())


__all__ = [
    "CALCULATION_VERSION",
    "DIFFICULTY_MULTIPLIERS",
    "NORMAL_CAP",
    "PROVISIONAL_CAP",
    "PROVISIONAL_THRESHOLD",
    "RATING_FLOOR",
    "STARTING_RATING",
    "FinalizedAttempt",
    "RatingProjection",
    "apply_rating_change",
    "compute_delta",
    "finalize_daily_ratings",
    "get_or_create_rating",
    "get_user_history",
    "get_user_rating",
    "project_for_attempt",
    "tier_for_rating",
]
