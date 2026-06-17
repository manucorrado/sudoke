from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings

def _engine_kwargs() -> dict:
    if settings.DATABASE_URL.startswith("sqlite"):
        return {}
    return {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    }


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,
    **_engine_kwargs(),
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
