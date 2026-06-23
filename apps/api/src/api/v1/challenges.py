"""Challenge endpoints (PRD §16, Epic 6).

Endpoints:

  - POST   /me/challenges                              (auth) create for current daily
  - GET    /me/challenges                              (auth) list sent + received
  - GET    /challenges/by-code/{code}                  (public) resolve invite
  - GET    /challenges/{challenge_id}                  (public) detail w/ acceptances
  - POST   /challenges/{challenge_id}/results          (any principal) record result
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.session import get_db
from src.middleware.principal import Principal, require_principal, require_user
from src.models import (
    Challenge,
    DailyPuzzle,
    RankedAttempt,
    User,
)
from src.schemas.common import (
    ChallengeAcceptancePublic,
    ChallengeCreateRequest,
    ChallengeDetailPublic,
    ChallengePublic,
    MyChallengesPublic,
)
from src.services.puzzles import get_active_daily_puzzle
from src.services.social import (
    SocialError,
    create_challenge,
    get_challenge,
    get_challenge_by_code,
    list_acceptances,
    list_my_challenges,
    record_acceptance,
)

router = APIRouter(prefix="/challenges", tags=["challenges"])
me_router = APIRouter(prefix="/me/challenges", tags=["challenges"])


def _share_url(code: str) -> str:
    base = settings.CHALLENGE_SHARE_BASE_URL.rstrip("/")
    return f"{base}/{code}"


def _social_error(exc: SocialError) -> HTTPException:
    return HTTPException(
        status_code=exc.http_status,
        detail={"code": exc.code, "message": exc.message},
    )


async def _challenger_attempt(
    session: AsyncSession, *, user: User, daily_id: uuid.UUID
) -> RankedAttempt | None:
    stmt = (
        select(RankedAttempt)
        .where(RankedAttempt.user_id == user.id)
        .where(RankedAttempt.daily_puzzle_id == daily_id)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def _user_by_id(
    session: AsyncSession, user_id: uuid.UUID
) -> User | None:
    return await session.get(User, user_id)


async def _public(
    session: AsyncSession, challenge: Challenge
) -> ChallengePublic:
    challenger = await _user_by_id(session, challenge.challenger_user_id)
    return ChallengePublic(
        id=challenge.id,
        code=challenge.code,
        daily_puzzle_id=challenge.daily_puzzle_id,
        challenger_user_id=challenge.challenger_user_id,
        challenger_username=challenger.username if challenger else None,
        challenger_display_name=(
            challenger.display_name if challenger else None
        ),
        challenger_duration_ms=challenge.challenger_duration_ms,
        challenger_mistakes=challenge.challenger_mistakes,
        status=challenge.status.value,
        created_at=challenge.created_at,
        expires_at=challenge.expires_at,
        share_url=_share_url(challenge.code),
    )


@me_router.post("", response_model=ChallengePublic)
async def create_my_challenge(
    payload: ChallengeCreateRequest,
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> ChallengePublic:
    daily: DailyPuzzle | None
    if payload.daily_puzzle_id is not None:
        daily = await session.get(DailyPuzzle, payload.daily_puzzle_id)
    else:
        daily = await get_active_daily_puzzle(session)
    if daily is None:
        raise HTTPException(status_code=404, detail="Daily puzzle not found")
    attempt = await _challenger_attempt(session, user=me, daily_id=daily.id)
    challenge = await create_challenge(
        session,
        challenger=me,
        daily=daily,
        challenger_attempt=attempt,
    )
    return await _public(session, challenge)


@me_router.get("", response_model=MyChallengesPublic)
async def list_mine(
    me: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> MyChallengesPublic:
    sent, received = await list_my_challenges(session, me)
    return MyChallengesPublic(
        sent=[await _public(session, c) for c in sent],
        received=[await _public(session, c) for c in received],
    )


@router.get("/by-code/{code}", response_model=ChallengeDetailPublic)
async def resolve_by_code(
    code: str,
    session: AsyncSession = Depends(get_db),
) -> ChallengeDetailPublic:
    challenge = await get_challenge_by_code(session, code)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return await _build_detail(session, challenge)


@router.get("/{challenge_id}", response_model=ChallengeDetailPublic)
async def get_detail(
    challenge_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ChallengeDetailPublic:
    challenge = await get_challenge(session, challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return await _build_detail(session, challenge)


@router.post(
    "/{challenge_id}/results", response_model=ChallengeAcceptancePublic
)
async def post_result(
    challenge_id: uuid.UUID,
    principal: Principal = Depends(require_principal),
    session: AsyncSession = Depends(get_db),
) -> ChallengeAcceptancePublic:
    challenge = await get_challenge(session, challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    attempt = None
    if principal.user is not None:
        attempt = await _challenger_attempt(
            session, user=principal.user, daily_id=challenge.daily_puzzle_id
        )
    try:
        acceptance = await record_acceptance(
            session,
            challenge=challenge,
            user=principal.user,
            guest=principal.guest,
            attempt=attempt,
        )
    except SocialError as exc:
        raise _social_error(exc) from exc
    return await _acceptance_public(session, acceptance)


async def _acceptance_public(
    session: AsyncSession, acc
) -> ChallengeAcceptancePublic:
    user = None
    if acc.recipient_user_id is not None:
        user = await _user_by_id(session, acc.recipient_user_id)
    return ChallengeAcceptancePublic(
        id=acc.id,
        challenge_id=acc.challenge_id,
        recipient_user_id=acc.recipient_user_id,
        recipient_username=user.username if user else None,
        recipient_display_name=user.display_name if user else None,
        duration_ms=acc.duration_ms,
        mistakes=acc.mistakes,
        completed_at=acc.completed_at,
    )


async def _build_detail(
    session: AsyncSession, challenge: Challenge
) -> ChallengeDetailPublic:
    daily = await session.get(DailyPuzzle, challenge.daily_puzzle_id)
    if daily is None or daily.puzzle is None:
        raise HTTPException(status_code=404, detail="Daily puzzle not found")
    acceptances = await list_acceptances(session, challenge.id)
    return ChallengeDetailPublic(
        challenge=await _public(session, challenge),
        acceptances=[
            await _acceptance_public(session, a) for a in acceptances
        ],
        daily_difficulty=daily.puzzle.difficulty,
        daily_scheduled_for=daily.scheduled_for,
    )
