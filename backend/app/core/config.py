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

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
    """Production: set FRONTEND_URL to your Vercel URL (e.g. https://career-os.vercel.app)."""
    FRONTEND_URL: str = ""
    """Optional regex for Vercel preview deploys, e.g. https://.*\\.vercel\\.app"""
    CORS_ORIGIN_REGEX: str = ""
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

    """Shared secret for optional POST /internal/cron/scheduled-scans (not required with UptimeRobot)."""
    CRON_SECRET: str = ""

    HEALTH_CACHE_SECONDS: float = 2.0
    SCHEDULER_HEARTBEAT_ENABLED: bool = True
    """Run overdue scans once on process start (after sleep/deploy). Disable if you only rely on APScheduler slots."""
    SCHEDULER_STARTUP_CATCHUP: bool = True

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

    @property
    def is_cloud_deploy(self) -> bool:
        """True on Render/Heroku-style hosts (auto CORS for Vercel frontends)."""
        return bool(os.getenv("RENDER")) or bool(os.getenv("RENDER_SERVICE_ID"))

    @property
    def effective_cors_origins(self) -> list[str]:
        """Merge configured origins with FRONTEND_URL and local dev hosts."""
        origins = list(self.CORS_ORIGINS)
        frontend = (self.FRONTEND_URL or "").strip().rstrip("/")
        if frontend and frontend not in origins:
            origins.append(frontend)
        # Known production frontend (demo) — also covered by vercel regex when deployed
        for origin in (
            "https://career-os-two-chi.vercel.app",
            "https://career-os.vercel.app",
        ):
            if origin not in origins:
                origins.append(origin)
        if not self.is_production and not self.is_cloud_deploy:
            for host in ("localhost", "127.0.0.1"):
                for port in (5173, 4173, 3000):
                    origin = f"http://{host}:{port}"
                    if origin not in origins:
                        origins.append(origin)
        return origins

    @property
    def effective_cors_origin_regex(self) -> str | None:
        regex = (self.CORS_ORIGIN_REGEX or "").strip()
        if regex:
            return regex
        if self.is_production or self.is_cloud_deploy:
            return r"https://.*\.vercel\.app"
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
