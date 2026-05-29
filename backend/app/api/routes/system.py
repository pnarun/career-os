"""Production health, metrics, and system status endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response

from app.api.routes.logs_view_html import render_logs_page
from app.api.routes.status_page_html import render_uptime_status_page
from app.core.cache import cache_get, cache_set, cache_key
from app.core.health_keepalive import build_detailed_health_payload, get_cached_health_payload
from app.api.routes.beta_ops_page_html import render_beta_ops_page
from app.services.beta_ops_service import beta_ops_snapshot
from app.core.log_buffer import log_buffer
from app.services.logs_view_service import (
    distinct_users,
    export_logs_csv,
    get_log_entries,
)
from app.core.circuit_breaker import circuit_breaker_status
from app.core.brand_assets import api_brand_logo_url, brand_logo_url_for_dark_page
from app.core.config import settings
from app.core.database import get_database
from app.core.metrics import metrics
from app.observability.operational_metrics import observability_snapshot
from app.core.runtime_diagnostics import process_memory_snapshot
from app.core.redis_client import redis_health
from app.realtime.websocket_manager import realtime_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/logs", status_code=302)


@router.head("/", include_in_schema=False)
async def root_head() -> Response:
    """Render's port probe uses HEAD / — return 200 to avoid false negatives."""
    return Response(status_code=200)


def _uptimerobot_status_url() -> str:
    page_url = (settings.UPTIMEROBOT_STATUS_PAGE_URL or "").strip()
    if not page_url:
        raise HTTPException(
            status_code=503,
            detail="UPTIMEROBOT_STATUS_PAGE_URL is not configured",
        )
    return page_url


@router.get("/uptime/go", include_in_schema=False)
async def uptime_status_redirect() -> RedirectResponse:
    """Redirect to the public UptimeRobot status page (iframe embedding is blocked)."""
    return RedirectResponse(url=_uptimerobot_status_url(), status_code=302)


@router.get("/uptime", response_class=HTMLResponse, include_in_schema=False)
async def uptime_status_viewer() -> HTMLResponse:
    """
    Developer hub: live API health + link to UptimeRobot status page.
    Override URL with UPTIMEROBOT_STATUS_PAGE_URL.
    """
    page_url = _uptimerobot_status_url()
    health = get_cached_health_payload(
        service=settings.APP_NAME,
        ttl_seconds=settings.HEALTH_CACHE_SECONDS,
    )
    system = await system_status()
    html = render_uptime_status_page(
        status_page_url=page_url,
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        logo_url=brand_logo_url_for_dark_page("full"),
        favicon_url=api_brand_logo_url("symbol"),
        health=health,
        system=system,
    )
    return HTMLResponse(html)


@router.get("/system/uptime", response_class=HTMLResponse, include_in_schema=True)
async def uptime_status_viewer_alias() -> HTMLResponse:
    """Alias for /uptime (visible in OpenAPI)."""
    return await uptime_status_viewer()


@router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
async def logs_viewer(
    limit: int = Query(default=200, ge=10, le=500),
    user: str = Query(default=""),
    level: str = Query(default=""),
) -> HTMLResponse:
    """Tabular log viewer with user filter and CSV export."""
    entries = get_log_entries(limit=limit, user_filter=user, level_filter=level)
    users = distinct_users(get_log_entries(limit=limit))
    html = render_logs_page(
        entries=entries,
        users=users,
        limit=limit,
        user_filter=user.strip(),
        level_filter=level.strip().upper(),
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        logo_url=brand_logo_url_for_dark_page("full"),
        favicon_url=api_brand_logo_url("symbol"),
    )
    return HTMLResponse(html)


@router.get("/logs/export", include_in_schema=False)
async def logs_export(
    limit: int = Query(default=500, ge=10, le=500),
    user: str = Query(default=""),
    level: str = Query(default=""),
) -> PlainTextResponse:
    entries = get_log_entries(limit=limit, user_filter=user, level_filter=level)
    csv_body = export_logs_csv(entries)
    return PlainTextResponse(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="career-os-logs.csv"',
        },
    )


@router.get("/logs/api", include_in_schema=False)
async def logs_api(
    limit: int = Query(default=200, ge=10, le=500),
    user: str = Query(default=""),
    level: str = Query(default=""),
) -> dict[str, Any]:
    entries = get_log_entries(limit=limit, user_filter=user, level_filter=level)
    return {
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "count": len(entries),
        "entries": entries,
        "lines": log_buffer.tail(limit),
    }


@router.get("/system/logs", response_class=HTMLResponse, include_in_schema=True)
async def logs_viewer_alias(
    limit: int = Query(default=200, ge=10, le=500),
    user: str = Query(default=""),
    level: str = Query(default=""),
) -> HTMLResponse:
    """Alias for /logs (visible in OpenAPI)."""
    return await logs_viewer(limit=limit, user=user, level=level)


@router.get("/system/logs/api", include_in_schema=True)
async def logs_api_alias(
    limit: int = Query(default=200, ge=10, le=500),
    user: str = Query(default=""),
    level: str = Query(default=""),
) -> dict[str, Any]:
    return await logs_api(limit=limit, user=user, level=level)


async def _mongo_health() -> dict[str, Any]:
    try:
        db = get_database()
        await db.command("ping")
        return {"status": "ok"}
    except Exception as exc:
        logger.debug("Mongo health check failed in system_status: %s", exc, exc_info=True)
        return {"status": "down", "error": str(exc)}


def _queue_health() -> dict[str, Any]:
    if not settings.CELERY_ENABLED:
        return {"status": "disabled", "backlog": 0}
    try:
        from app.core.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=1.0)
        active = inspect.active() if inspect else None
        backlog = sum(len(v or []) for v in (active or {}).values()) if active else 0
        return {"status": "ok", "backlog": backlog}
    except Exception as exc:
        logger.warning(
            "Celery queue health check failed: %s",
            exc,
            exc_info=True,
            extra={"event": "queue_health", "status": "degraded"},
        )
        return {"status": "degraded", "backlog": 0, "error": str(exc)}


class DeployNotifyRequest(BaseModel):
    component: str = Field(..., description="e.g. render-api, vercel-frontend, github-ci")
    status: str = Field(default="success", description="success or failed")
    url: str = ""
    message: str = ""


def _require_internal_secret(x_cron_secret: str) -> None:
    secret = (settings.CRON_SECRET or "").strip()
    if not secret or x_cron_secret != secret:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/internal/notify/deploy", include_in_schema=False)
async def notify_deploy(
    payload: DeployNotifyRequest,
    x_cron_secret: str = Header(default="", alias="X-Cron-Secret"),
) -> dict[str, Any]:
    """
    Webhook for deploy success (Render/Vercel/GitHub Actions).
    Set ADMIN_NOTIFY_EMAIL on the API and call with header X-Cron-Secret.
    """
    _require_internal_secret(x_cron_secret)
    from app.services.admin_notify_service import notify_deploy_event

    sent = notify_deploy_event(
        component=payload.component.strip(),
        status=payload.status.strip(),
        url=payload.url.strip(),
        message=payload.message.strip(),
    )
    return {"status": "ok", "email_sent": sent}


@router.post("/internal/cron/scheduled-scans", include_in_schema=False)
async def cron_scheduled_scans(
    x_cron_secret: str = Header(default="", alias="X-Cron-Secret"),
) -> dict[str, Any]:
    """
    Trigger overdue scheduled scans (Render cron). Requires CRON_SECRET on the API
    and the same value in X-Cron-Secret.
    """
    _require_internal_secret(x_cron_secret)

    from app.services.scheduler_service import run_overdue_scheduled_scans

    return await run_overdue_scheduled_scans()


def _log_health_ping_if_debug() -> None:
    if settings.ENVIRONMENT == "development" or settings.LOG_LEVEL.upper() == "DEBUG":
        logger.debug("[HEALTH] keepalive ping")


@router.head("/health")
async def health_head() -> Response:
    """UptimeRobot free tier uses HEAD — empty 200, no DB or scheduler work."""
    _log_health_ping_if_debug()
    return Response(status_code=200)


@router.get("/health")
async def health_get(
    detail: bool = Query(False, description="Include mongo, websocket, scan & provider subsystems"),
) -> dict[str, Any]:
    """Health check. Default is minimal keep-alive; ?detail=1 for beta subsystem snapshot."""
    _log_health_ping_if_debug()
    if detail:
        return await build_detailed_health_payload(service=settings.APP_NAME)
    return get_cached_health_payload(
        service=settings.APP_NAME,
        ttl_seconds=settings.HEALTH_CACHE_SECONDS,
    )


@router.get("/system/beta-ops", response_class=HTMLResponse, include_in_schema=False)
async def beta_ops_viewer() -> HTMLResponse:
    """Lightweight HTML ops dashboard for beta (JSON at /system/beta-ops/json)."""
    health = await build_detailed_health_payload(service=settings.APP_NAME)
    ops = await beta_ops_snapshot()
    html = render_beta_ops_page(
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        logo_url=brand_logo_url_for_dark_page("full"),
        favicon_url=api_brand_logo_url("symbol"),
        system=health,
        ops=ops,
    )
    return HTMLResponse(html)


@router.get("/system/beta-ops/json", include_in_schema=True)
async def beta_ops_json() -> dict[str, Any]:
    """JSON operational snapshot for beta monitoring."""
    return {
        "health": await build_detailed_health_payload(service=settings.APP_NAME),
        "ops": await beta_ops_snapshot(),
    }


@router.get("/system/metrics")
async def system_metrics() -> dict[str, Any]:
    cached = cache_get(cache_key("system", "metrics"))
    if cached:
        return cached

    payload = {
        **observability_snapshot(),
        "websocket_connections": realtime_manager.total_connections(),
        "environment": settings.ENVIRONMENT,
    }
    cache_set(cache_key("system", "metrics"), payload, ttl_seconds=15)
    return payload


@router.get("/system/status")
async def system_status() -> dict[str, Any]:
    mongo = await _mongo_health()
    redis = redis_health()
    queue = _queue_health()
    circuits = circuit_breaker_status()

    status = "ok"
    if mongo["status"] != "ok":
        status = "degraded"
    if settings.REDIS_ENABLED and redis.get("status") == "down":
        status = "degraded"

    return {
        "status": status,
        "environment": settings.ENVIRONMENT,
        "components": {
            "mongodb": mongo,
            "redis": redis,
            "queue": queue,
            "websocket": {
                "status": "ok",
                "connections": realtime_manager.total_connections(),
            },
            "automation": {"status": "ok", "mode": settings.AUTOMATION_WORKER_MODE},
            "circuit_breakers": circuits,
        },
        "features": {
            "celery": settings.CELERY_ENABLED,
            "redis": settings.REDIS_ENABLED,
            "rate_limit": settings.RATE_LIMIT_ENABLED,
            "queue_scans": settings.QUEUE_SCANS_ENABLED,
            "enable_scheduler": settings.ENABLE_SCHEDULER,
            "enable_playwright": settings.ENABLE_PLAYWRIGHT,
            "enable_realtime": settings.ENABLE_REALTIME,
            "enable_automation": settings.ENABLE_AUTOMATION,
            "scheduler_startup_catchup": settings.SCHEDULER_STARTUP_CATCHUP,
        },
        "process_memory": process_memory_snapshot(),
        "service_mode": settings.SERVICE_MODE,
    }
