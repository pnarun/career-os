import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

EnvironmentName = Literal["development", "staging", "production"]


def _env_files() -> tuple[str, ...]:
    env = os.getenv("ENVIRONMENT", "development").lower()
    files: list[str] = []
    for name in (f".env.{env}", ".env"):
        if os.path.isfile(name):
            files.append(name)
    return tuple(files) if files else (".env",)


class Settings(BaseSettings):
    APP_NAME: str = "Career OS API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: EnvironmentName = "development"
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True

    MONGO_URI: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True

    # Infrastructure toggles
    CELERY_ENABLED: bool = False
    QUEUE_SCANS_ENABLED: bool = False
    RATE_LIMIT_ENABLED: bool = True
    AUTOMATION_WORKER_MODE: str = "subprocess"

    GEMINI_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_SLOW_MO: int = 0
    PLAYWRIGHT_VIEWPORT_WIDTH: int = 1280
    PLAYWRIGHT_VIEWPORT_HEIGHT: int = 720
    PLAYWRIGHT_USER_AGENT: str = ""
    PLAYWRIGHT_DEFAULT_TIMEOUT_MS: int = 30_000

    ASSISTED_APPLY_ENABLED: bool = False
    INTERVIEW_WEB_QUESTIONS_ENABLED: bool = True

    JWT_SECRET_KEY: str = "change-me-in-production-use-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    LEGACY_MIGRATION_EMAIL: str = "legacy@career-os.local"
    LEGACY_MIGRATION_PASSWORD: str = "ChangeMe123!"
    AUTH_SEED_DEMO_USERS: bool = False

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_OAUTH_REDIRECT_URI: str = ""

    AUTH_DEV_EXPOSE_OTP: bool = False

    # Cache TTLs (seconds)
    CACHE_PROVIDER_TTL: int = 300
    CACHE_ANALYTICS_TTL: int = 600
    CACHE_COPILOT_TTL: int = 300

    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
