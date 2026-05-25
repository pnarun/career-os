"""Production health, metrics, and system status endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from app.core.cache import cache_get, cache_set, cache_key
from app.core.circuit_breaker import circuit_breaker_status
from app.core.config import settings
from app.core.database import get_database
from app.core.metrics import metrics
from app.core.redis_client import redis_health
from app.realtime.websocket_manager import realtime_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


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
