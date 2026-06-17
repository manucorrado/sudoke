from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.middleware.principal import require_user
from src.models import User
from src.schemas.common import MeResponse, UpdateProfileRequest
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
