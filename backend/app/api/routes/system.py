"""Production health, metrics, and system status endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse

from app.api.routes.logs_view_html import render_logs_page
from app.core.cache import cache_get, cache_set, cache_key
from app.core.health_keepalive import get_cached_health_payload
from app.core.log_buffer import log_buffer
from app.services.logs_view_service import (
    distinct_users,
    export_logs_csv,
    get_log_entries,
)
from app.core.circuit_breaker import circuit_breaker_status
from app.core.config import settings
from app.core.database import get_database
from app.core.metrics import metrics
from app.core.redis_client import redis_health
from app.realtime.websocket_manager import realtime_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/logs", status_code=302)


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
        return {"status": "degraded", "backlog": 0, "error": str(exc)}


@router.post("/internal/cron/scheduled-scans", include_in_schema=False)
async def cron_scheduled_scans(
    x_cron_secret: str = Header(default="", alias="X-Cron-Secret"),
) -> dict[str, Any]:
    """
    Trigger overdue scheduled scans (Render cron). Requires CRON_SECRET on the API
    and the same value in X-Cron-Secret.
    """
    secret = (settings.CRON_SECRET or "").strip()
    if not secret or x_cron_secret != secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    from app.services.scheduler_service import run_overdue_scheduled_scans

    return await run_overdue_scheduled_scans()


@router.get("/health")
async def health() -> dict[str, Any]:
    """
    UptimeRobot / keep-alive endpoint: no DB, no auth, no scans.
    Use GET /system/status for full dependency checks.
    """
    return get_cached_health_payload(
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        ttl_seconds=settings.HEALTH_CACHE_SECONDS,
    )


@router.get("/system/metrics")
async def system_metrics() -> dict[str, Any]:
    cached = cache_get(cache_key("system", "metrics"))
    if cached:
        return cached

    payload = {
        **metrics.snapshot(),
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
        },
    }
