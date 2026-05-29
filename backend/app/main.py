import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from app.auth.dependencies import get_current_user
from app.auth.routes import router as auth_router
from app.realtime.realtime_router import router as realtime_router
from app.realtime.redis_bridge import start_realtime_subscriber
from app.api.routes import db as db_routes
from app.api.routes import jobs as jobs_routes
from app.api.routes import match as match_routes
from app.api.routes import preferences as preferences_routes
from app.api.routes import resumes as resumes_routes
from app.api.routes import scan as scan_routes
from app.api.routes import scans as scans_routes
from app.api.routes import applications as applications_routes
from app.api.routes import automation as automation_routes
from app.api.routes import scan_analytics as scan_analytics_routes
from app.api.routes import upload as upload_routes
from app.api.routes import notifications as notifications_routes
from app.api.routes import auto_apply as auto_apply_routes
from app.api.routes import resume_ai as resume_ai_routes
from app.api.routes import career_analytics as career_analytics_routes
from app.api.routes import copilot as copilot_routes
from app.api.routes import interview_ai as interview_ai_routes
from app.api.routes import dashboard as dashboard_routes
from app.api.routes import suggestions as suggestions_routes
from app.api.routes import system as system_routes
from app.db.indexes import ensure_all_mongo_indexes
from app.services.automation_service import shutdown_automation
from app.services.migration_service import run_legacy_data_migration, seed_demo_users
from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo
from app.core.logging_config import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.user_context_middleware import UserContextMiddleware
from app.core.startup_banner import log_startup_banner
from app.observability.api_latency_middleware import ApiLatencyMiddleware
from app.core.redis_client import close_redis, get_redis
from app.services.scheduler_service import shutdown_scheduler, start_scheduler

configure_logging(service="career-os-api", level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    realtime_task = None
    try:
        log_startup_banner()
        logger.info(
            "Starting Career OS API environment=%s",
            settings.ENVIRONMENT,
            extra={"event": "startup", "status": "starting"},
        )
        await connect_to_mongo()
        get_redis()
        from app.services.cache_service import init_upstash_cache

        init_upstash_cache()
        await ensure_all_mongo_indexes()
        await run_legacy_data_migration()
        await seed_demo_users()

        if settings.ENABLE_SCHEDULER:
            await start_scheduler()
        else:
            logger.info(
                "[STARTUP] ENABLE_SCHEDULER=false — APScheduler not started",
                extra={"event": "startup", "scheduler": "disabled"},
            )

        if settings.ENABLE_REALTIME:
            realtime_task = await start_realtime_subscriber()
            logger.info(
                "[STARTUP] Realtime subscriber state=%s",
                "started" if realtime_task else "in_process_only",
                extra={"event": "startup", "realtime": "enabled"},
            )
        else:
            logger.info(
                "[STARTUP] ENABLE_REALTIME=false — Redis subscriber not started",
                extra={"event": "startup", "realtime": "disabled"},
            )

        from app.core.startup_checks import log_startup_verification

        await log_startup_verification()
        logger.info("Application ready", extra={"event": "startup", "status": "ok"})
    except Exception:
        logger.exception(
            "Failed to initialize application on startup",
            extra={"event": "startup", "status": "failed"},
        )
        raise
    yield
    if realtime_task:
        realtime_task.cancel()
    if settings.ENABLE_SCHEDULER:
        await shutdown_scheduler()
    if settings.ENABLE_AUTOMATION:
        await shutdown_automation()
    close_redis()
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if (not settings.is_production or settings.is_cloud_deploy) else None,
    redoc_url="/redoc" if (not settings.is_production or settings.is_cloud_deploy) else None,
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(ApiLatencyMiddleware)
app.add_middleware(RateLimitMiddleware)
_cors_kwargs: dict = {
    "allow_origins": settings.effective_cors_origins,
    "allow_credentials": settings.CORS_ALLOW_CREDENTIALS,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["*"],
}
if settings.effective_cors_origin_regex:
    _cors_kwargs["allow_origin_regex"] = settings.effective_cors_origin_regex
app.add_middleware(CORSMiddleware, **_cors_kwargs)
app.add_middleware(UserContextMiddleware)

logger.info(
    "CORS enabled origins=%s regex=%s cloud=%s",
    settings.effective_cors_origins,
    settings.effective_cors_origin_regex,
    settings.is_cloud_deploy,
)

_auth = [Depends(get_current_user)]

_brand_static = Path(__file__).resolve().parent / "static" / "brand"
if _brand_static.is_dir():
    app.mount("/brand", StaticFiles(directory=str(_brand_static)), name="brand")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    """Browsers request /favicon.ico on API tabs (docs, /logs, /uptime)."""
    icon = _brand_static / "career-os-logo-symbol.png"
    if not icon.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(icon, media_type="image/png")


app.include_router(system_routes.router)
app.include_router(auth_router)
app.include_router(realtime_router)
app.include_router(db_routes.router)
app.include_router(upload_routes.router, dependencies=_auth)
app.include_router(match_routes.router, dependencies=_auth)
app.include_router(dashboard_routes.router, dependencies=_auth)
app.include_router(jobs_routes.router, dependencies=_auth)
app.include_router(applications_routes.router, dependencies=_auth)
app.include_router(preferences_routes.router, dependencies=_auth)
app.include_router(suggestions_routes.router, dependencies=_auth)
app.include_router(resumes_routes.router, dependencies=_auth)
app.include_router(scan_routes.router, dependencies=_auth)
app.include_router(scans_routes.router, dependencies=_auth)
app.include_router(scan_analytics_routes.router, dependencies=_auth)
app.include_router(automation_routes.router, dependencies=_auth)
app.include_router(automation_routes.public_router)
app.include_router(notifications_routes.router, dependencies=_auth)
app.include_router(auto_apply_routes.router, dependencies=_auth)
app.include_router(resume_ai_routes.router, dependencies=_auth)
app.include_router(interview_ai_routes.router, dependencies=_auth)
app.include_router(career_analytics_routes.router, dependencies=_auth)
app.include_router(copilot_routes.router, dependencies=_auth)
