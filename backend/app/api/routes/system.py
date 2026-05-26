"""Production health, metrics, and system status endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.cache import cache_get, cache_set, cache_key
from app.core.log_buffer import log_buffer
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
) -> HTMLResponse:
    """Live tail of recent API logs (same stream as Render dashboard)."""
    lines = log_buffer.tail(limit)
    body = "\n".join(lines) if lines else "(no logs captured yet — trigger API traffic)"
    escaped = (
        body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta http-equiv="refresh" content="5"/>
  <title>Career OS — Logs</title>
  <style>
    body {{ margin:0; background:#0f172a; color:#e2e8f0; font-family:ui-monospace,monospace; font-size:12px; }}
    header {{ padding:12px 16px; background:#1e293b; border-bottom:1px solid #334155; display:flex; gap:16px; align-items:center; flex-wrap:wrap; }}
    header a {{ color:#818cf8; }}
    pre {{ margin:0; padding:16px; white-space:pre-wrap; word-break:break-word; line-height:1.45; }}
    .meta {{ color:#94a3b8; font-size:11px; }}
  </style>
</head>
<body>
  <header>
    <strong>Career OS API Logs</strong>
    <span class="meta">{settings.APP_NAME} · {settings.ENVIRONMENT} · {len(lines)} lines · auto-refresh 5s</span>
    <a href="/logs?limit={limit}">Refresh</a>
    <a href="/logs/api?limit={limit}">JSON</a>
    <a href="/health">Health</a>
    <a href="/docs">Docs</a>
  </header>
  <pre>{escaped}</pre>
</body>
</html>"""
    return HTMLResponse(html)


@router.get("/logs/api", include_in_schema=False)
async def logs_api(
    limit: int = Query(default=200, ge=10, le=500),
) -> dict[str, Any]:
    lines = log_buffer.tail(limit)
    return {
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "count": len(lines),
        "lines": lines,
    }


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


@router.get("/health")
async def health() -> dict[str, Any]:
    mongo = await _mongo_health()
    redis = redis_health()
    overall = "ok"
    if mongo["status"] != "ok":
        overall = "degraded"
    if settings.REDIS_ENABLED and redis.get("status") not in ("ok", "disabled"):
        overall = "degraded"
    return {
        "status": overall,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


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
