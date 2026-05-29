import os
from functools import lru_cache
import sys
from typing import Literal

from pydantic import model_validator
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

    """Ops inbox: new signups, deploy alerts (also set in GitHub Secrets for CI)."""
    ADMIN_NOTIFY_EMAIL: str = ""
    ADMIN_NOTIFY_ENABLED: bool = True

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
    """Public UptimeRobot status page (embedded at GET /uptime for developers)."""
    UPTIMEROBOT_STATUS_PAGE_URL: str = "https://stats.uptimerobot.com/rIhbIgCMm7"
    """Public API base URL for absolute brand links in email (optional; Render sets RENDER_EXTERNAL_URL)."""
    API_PUBLIC_URL: str = ""
    """Optional Cloudinary CDN URLs (set after running scripts/upload_brand_logos.py)."""
    BRAND_LOGO_FULL_URL: str = ""
    BRAND_LOGO_BLACK_URL: str = ""
    BRAND_LOGO_SYMBOL_URL: str = ""
    SCHEDULER_HEARTBEAT_ENABLED: bool = True
    """Run overdue scans once on process start (after sleep/deploy). Disable if you only rely on APScheduler slots."""
    SCHEDULER_STARTUP_CATCHUP: bool = True

    # Phase 0 — runtime feature flags (all default true; set false to disable subsystems)
    SERVICE_MODE: str = "api"
    ENABLE_SCHEDULER: bool = True
    ENABLE_PLAYWRIGHT: bool = True
    ENABLE_REALTIME: bool = True
    ENABLE_AUTOMATION: bool = True

    # Phase 1A/1B — scan execution isolation (inline = monolith default; dispatch = worker queue)
    SCAN_EXECUTION_MODE: str = "inline"
    SCAN_WORKER_POLL_SECONDS: float = 8.0
    SCAN_WORKER_MAX_CONCURRENT: int = 1
    SCAN_WORKER_HEARTBEAT_SECONDS: float = 60.0
    SCAN_TASK_CLAIM_TIMEOUT_SECONDS: int = 300
    SCAN_TASK_EXECUTION_TIMEOUT_SECONDS: int = 7200

    # Phase 6 — Mongo cross-service realtime bridge (API only)
    REALTIME_BRIDGE_ENABLED: bool = True
    REALTIME_BRIDGE_POLL_SECONDS: float = 1.5
    REALTIME_BRIDGE_BATCH_SIZE: int = 32

    # Upstash Redis REST (response caching)
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    # Cache TTLs (seconds)
    CACHE_PROVIDER_TTL: int = 300
    CACHE_ANALYTICS_TTL: int = 600
    CACHE_COPILOT_TTL: int = 300
    CACHE_RESPONSE_TTL: int = 300  # dashboard, career analytics, scan summaries

    # MongoDB performance
    MONGO_SLOW_QUERY_MS: float = 500.0
    MONGO_EXPLAIN_QUERIES: bool = False
    MONGO_ANALYTICS_HISTORY_LIMIT: int = 1500

    # Provider fetch resilience
    PROVIDER_FETCH_TIMEOUT_SECONDS: float = 90.0
    PROVIDER_FETCH_MAX_RETRIES: int = 1

    # API observability
    API_SLOW_REQUEST_MS: float = 1500.0

    # Background scan state
    SCAN_STALE_SECONDS: int = 7200

    """Minimum Career Lens extension version accepted for connect/resync."""
    EXTENSION_MIN_VERSION: str = "0.3.0"
    WEBSOCKET_MAX_CONNECTIONS_PER_USER: int = 5
    WEBSOCKET_MAX_CONNECTIONS_TOTAL: int = 200

    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _disable_local_redis_on_cloud(self) -> "Settings":
        """Render has no localhost Redis — avoid connect spam if env was mis-set."""
        if not self.REDIS_ENABLED:
            return self
        url = (self.REDIS_URL or "").lower()
        points_local = "localhost" in url or "127.0.0.1" in url
        if points_local and (self.is_production or self.is_cloud_deploy):
            object.__setattr__(self, "REDIS_ENABLED", False)
        return self

    @property
    def admin_notify_email(self) -> str:
        explicit = (self.ADMIN_NOTIFY_EMAIL or "").strip()
        if explicit:
            return explicit
        return (self.LEGACY_MIGRATION_EMAIL or "").strip()

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_cloud_deploy(self) -> bool:
        """True on Render/Heroku-style hosts (auto CORS for Vercel frontends)."""
        return bool(os.getenv("RENDER")) or bool(os.getenv("RENDER_SERVICE_ID"))

    @property
    def headed_session_prep_available(self) -> bool:
        """Interactive Prepare session (visible Chromium) — local backend only."""
        if self.is_cloud_deploy:
            return False
        if sys.platform == "linux" and not (
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        ):
            return False
        return True

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
