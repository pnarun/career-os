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
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.user_context_middleware import UserContextMiddleware
from app.observability.api_latency_middleware import ApiLatencyMiddleware
from app.runtime.bootstrap import bootstrap_api_subsystems, bootstrap_core, shutdown_api_subsystems

configure_logging(service="career-os-api", level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    realtime_task = None
    try:
        await bootstrap_core()
        realtime_task = await bootstrap_api_subsystems()
        logger.info("Application ready", extra={"event": "startup", "status": "ok"})
    except Exception:
        logger.exception(
            "Failed to initialize application on startup",
            extra={"event": "startup", "status": "failed"},
        )
        raise
    yield
    await shutdown_api_subsystems(realtime_task)


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
