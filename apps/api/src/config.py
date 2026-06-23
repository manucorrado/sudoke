from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/sudoke"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    SENTRY_DSN: str | None = None
    CLERK_SECRET_KEY: str | None = None
    CLERK_PUBLISHABLE_KEY: str | None = None
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Base URL for human-readable challenge share links. The mobile app
    # also handles `sudoke://c/{code}` deep links — see /c/[code].
    CHALLENGE_SHARE_BASE_URL: str = "https://sudoke.app/c"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
