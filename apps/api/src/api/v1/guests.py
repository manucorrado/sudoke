from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.common import CreateGuestRequest, GuestSessionResponse
from src.services.users import create_guest_session

router = APIRouter(prefix="/guest", tags=["guest"])


@router.post("/sessions", response_model=GuestSessionResponse, status_code=201)
async def create_guest(
    payload: CreateGuestRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> GuestSessionResponse:
    user_agent = payload.user_agent or request.headers.get("user-agent")
    guest = await create_guest_session(
        session, user_agent=user_agent, locale=payload.locale
    )
    return GuestSessionResponse.model_validate(guest)
