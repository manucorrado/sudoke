from typing import Any

import structlog
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from src.config import settings
from src.db.session import engine

logger = structlog.get_logger()

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@router.get("/ready")
async def readiness_check() -> JSONResponse:
    checks: dict[str, Any] = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        logger.exception("Database readiness check failed")
        checks["database"] = "unavailable"

    try:
        redis = Redis.from_url(settings.REDIS_URL)
        try:
            await redis.ping()
            checks["redis"] = "ok"
        finally:
            await redis.aclose()
    except Exception:
        logger.exception("Redis readiness check failed")
        checks["redis"] = "unavailable"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ok" if all_ok else "degraded", "checks": checks},
    )
