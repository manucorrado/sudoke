from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/sudoke"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    SENTRY_DSN: str | None = None
    CLERK_SECRET_KEY: str | None = None
    CLERK_PUBLISHABLE_KEY: str | None = None
    CLERK_JWKS_URL: str | None = None
    CLERK_ISSUER: str | None = None
    CLERK_JWT_AUDIENCE: str | None = None
    CLERK_WEBHOOK_SIGNING_SECRET: str | None = None
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ALLOWED_ORIGINS: str = ""
    POSTHOG_API_KEY: str | None = None
    POSTHOG_HOST: str | None = None
    EXPO_ACCESS_TOKEN: str | None = None

    # Base URL for human-readable challenge share links. The mobile app
    # also handles `sudoke://c/{code}` deep links — see /c/[code].
    CHALLENGE_SHARE_BASE_URL: str = "https://sudoke.app/c"

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Render Postgres URLs need the asyncpg SQLAlchemy driver suffix."""

        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def cors_allowed_origins(self) -> list[str]:
        if self.is_development:
            return ["*"]
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def clerk_jwks_url(self) -> str | None:
        if self.CLERK_JWKS_URL:
            return self.CLERK_JWKS_URL
        if self.CLERK_ISSUER:
            return f"{self.CLERK_ISSUER.rstrip('/')}/.well-known/jwks.json"
        return None


settings = Settings()
