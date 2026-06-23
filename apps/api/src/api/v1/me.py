from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.principal import require_user
from src.models import User
from src.schemas.common import (
    MeResponse,
    NotificationPreferencesPublic,
    StreakPublic,
    UpdateNotificationPreferencesRequest,
    UpdateProfileRequest,
)
from src.services.streaks import (
    MAX_FREEZES_HELD,
    get_or_create_notification_preferences,
    sync_to_today,
)
from src.services.users import update_profile

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeResponse)
async def read_me(user: User = Depends(require_user)) -> User:
    return user


@router.patch("/profile", response_model=MeResponse)
async def patch_profile(
    payload: UpdateProfileRequest,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> User:
    try:
        return await update_profile(session, user, payload)
    except ValueError as exc:
        if str(exc) == "username_taken":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            ) from exc
        raise


@router.get("/streak", response_model=StreakPublic)
async def read_streak(
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> StreakPublic:
    today = datetime.now(timezone.utc).date()
    streak = await sync_to_today(session, user, today=today)
    return StreakPublic(
        current_length=streak.current_length,
        longest_length=streak.longest_length,
        freezes_held=streak.freezes_held,
        max_freezes=MAX_FREEZES_HELD,
        completions_total=streak.completions_total,
        last_completed_date=streak.last_completed_date,
        streak_started_date=streak.streak_started_date,
    )


@router.get(
    "/notifications/preferences",
    response_model=NotificationPreferencesPublic,
)
async def get_notification_preferences(
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> NotificationPreferencesPublic:
    prefs = await get_or_create_notification_preferences(session, user)
    return NotificationPreferencesPublic.model_validate(prefs)


@router.patch(
    "/notifications/preferences",
    response_model=NotificationPreferencesPublic,
)
async def patch_notification_preferences(
    payload: UpdateNotificationPreferencesRequest,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> NotificationPreferencesPublic:
    prefs = await get_or_create_notification_preferences(session, user)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(prefs, field, value)
    return NotificationPreferencesPublic.model_validate(prefs)
