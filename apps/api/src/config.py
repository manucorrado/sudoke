from pydantic import field_validator
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

    # Comma-separated list of browser origins allowed by CORS in non-dev
    # environments (e.g. the admin dashboard). Native mobile clients are
    # not CORS-gated. In development all origins are allowed.
    CORS_ALLOWED_ORIGINS: str = ""

    # Honors the X-Dev-Auth-User bypass header outside of development.
    # Must remain false in production; may be enabled in staging until
    # Clerk auth is wired end-to-end.
    ADMIN_DEV_BYPASS_ENABLED: bool = False

    # Base URL for human-readable challenge share links. The mobile app
    # also handles `sudoke://c/{code}` deep links — see /c/[code].
    CHALLENGE_SHARE_BASE_URL: str = "https://sudoke.app/c"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Coerce managed Postgres URLs to the asyncpg driver.

        Render exposes connection strings as ``postgres://`` or
        ``postgresql://`` without a driver suffix, but the SQLAlchemy async
        engine requires ``postgresql+asyncpg://``. Other schemes (sqlite,
        already-qualified asyncpg URLs) are left untouched.
        """
        import sys

        scheme = value.split("://")[0] if "://" in value else "(no scheme)"
        print(
            f"DATABASE_URL diagnostic: scheme={scheme!r}, "
            f"len={len(value)}, has_at={'@' in value}, "
            f"first_20={value[:20]!r}",
            file=sys.stderr,
        )

        if value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value[len("postgres://") :]
        if value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value[len("postgresql://") :]
        return value

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def cors_origins(self) -> list[str]:
        if self.is_development:
            return ["*"]
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
