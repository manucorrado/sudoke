from fastapi import APIRouter

from src.api.v1.admin_puzzles import router as admin_router
from src.api.v1.archive import router as archive_router
from src.api.v1.challenges import me_router as me_challenges_router
from src.api.v1.challenges import router as challenges_router
from src.api.v1.daily import attempt_router, router as daily_router
from src.api.v1.friends import router as friends_router
from src.api.v1.friends import users_router
from src.api.v1.guests import router as guests_router
from src.api.v1.health import router as health_router
from src.api.v1.leaderboards import rating_router, router as leaderboards_router
from src.api.v1.me import router as me_router

v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(me_router)
v1_router.include_router(rating_router)
v1_router.include_router(guests_router)
v1_router.include_router(daily_router)
v1_router.include_router(leaderboards_router)
v1_router.include_router(attempt_router)
v1_router.include_router(admin_router)
v1_router.include_router(archive_router)
v1_router.include_router(friends_router)
v1_router.include_router(users_router)
v1_router.include_router(challenges_router)
v1_router.include_router(me_challenges_router)
