import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.api.routes import system as system_routes
from app.services.application_service import ensure_application_indexes
from app.services.auto_apply.apply_history_service import ensure_apply_indexes
from app.services.automation_service import shutdown_automation
from app.services.career_insight_service import ensure_career_insight_indexes
from app.services.copilot.insight_memory_service import ensure_copilot_indexes
from app.services.interview_ai.prep_progress_service import ensure_prep_indexes
from app.services.interview_ai.web_question_service import ensure_web_question_cache_indexes
from app.services.notification_service import ensure_notification_indexes
from app.services.migration_service import run_legacy_data_migration, seed_demo_users
from app.services.user_service import ensure_user_indexes
from app.services.workspace_service import ensure_workspace_indexes
from app.services.user_preferences_service import ensure_preferences_indexes
from app.services.scan_session_service import ensure_scan_session_indexes
from app.services.job_service import ensure_job_indexes
from app.auth.service import ensure_auth_indexes
from app.auth.password_reset_service import ensure_password_reset_indexes
from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo
from app.core.logging_config import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.redis_client import close_redis, get_redis
from app.services.scheduler_service import shutdown_scheduler, start_scheduler

configure_logging(service="career-os-api", level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    realtime_task = None
    try:
        logger.info(
            "Starting Career OS API environment=%s",
            settings.ENVIRONMENT,
            extra={"event": "startup", "status": "starting"},
        )
        await connect_to_mongo()
        get_redis()
        await ensure_user_indexes()
        await ensure_workspace_indexes()
        await ensure_auth_indexes()
        await ensure_preferences_indexes()
        await ensure_scan_session_indexes()
        await ensure_job_indexes()
        await ensure_application_indexes()
        await ensure_notification_indexes()
        await ensure_career_insight_indexes()
        await ensure_apply_indexes()
        await ensure_prep_indexes()
        await ensure_copilot_indexes()
        await ensure_web_question_cache_indexes()
        await ensure_password_reset_indexes()
        await run_legacy_data_migration()
        await seed_demo_users()
        await start_scheduler()
        realtime_task = await start_realtime_subscriber()
        logger.info("Application ready", extra={"event": "startup", "status": "ok"})
    except Exception:
        logger.exception("Failed to initialize application on startup")
        raise
    yield
    if realtime_task:
        realtime_task.cancel()
    await shutdown_scheduler()
    await shutdown_automation()
    close_redis()
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

_auth = [Depends(get_current_user)]

app.include_router(system_routes.router)
app.include_router(auth_router)
app.include_router(realtime_router)
app.include_router(db_routes.router)
app.include_router(upload_routes.router, dependencies=_auth)
app.include_router(match_routes.router, dependencies=_auth)
app.include_router(jobs_routes.router, dependencies=_auth)
app.include_router(applications_routes.router, dependencies=_auth)
app.include_router(preferences_routes.router, dependencies=_auth)
app.include_router(resumes_routes.router, dependencies=_auth)
app.include_router(scan_routes.router, dependencies=_auth)
app.include_router(scan_analytics_routes.router, dependencies=_auth)
app.include_router(automation_routes.router, dependencies=_auth)
app.include_router(notifications_routes.router, dependencies=_auth)
app.include_router(auto_apply_routes.router, dependencies=_auth)
app.include_router(resume_ai_routes.router, dependencies=_auth)
app.include_router(interview_ai_routes.router, dependencies=_auth)
app.include_router(career_analytics_routes.router, dependencies=_auth)
app.include_router(copilot_routes.router, dependencies=_auth)
