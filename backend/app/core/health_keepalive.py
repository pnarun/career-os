"""Ultra-light /health payload for UptimeRobot and frontend keep-alive pings."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.config import settings
from app.core.database import get_database
from app.core.runtime_diagnostics import process_memory_snapshot
from app.observability.operational_metrics import observability_snapshot
from app.realtime.websocket_manager import realtime_manager
from app.services.beta_ops_service import provider_health_from_metrics, scan_subsystem_summary

logger = logging.getLogger(__name__)

_cache: dict[str, Any] | None = None
_cache_at: float = 0.0


def _scheduler_status() -> str:
    """Read scheduler state without calling get_scheduler() (no init)."""
    try:
        from app.services import scheduler_service

        sched = scheduler_service._scheduler
        if sched is not None and sched.running:
            return "running"
    except Exception:
        pass
    return "stopped"


def build_health_payload(*, service: str, redis_connected: bool | None = None) -> dict[str, Any]:
    """No DB, no auth, no scans — minimal fields for keep-alive."""
    if redis_connected is None:
        try:
            from app.services.cache_service import is_connected

            redis_connected = is_connected()
        except Exception:
            redis_connected = False

    return {
        "status": "ok",
        "service": service,
        "scheduler": _scheduler_status(),
        "redis_connected": bool(redis_connected),
    }


def get_cached_health_payload(
    *,
    service: str,
    ttl_seconds: float = 2.0,
) -> dict[str, Any]:
    global _cache, _cache_at

    now = time.monotonic()
    if _cache is not None and (now - _cache_at) < ttl_seconds:
        return dict(_cache)

    payload = build_health_payload(service=service)
    _cache = payload
    _cache_at = now
    return payload


_detail_cache: dict[str, Any] | None = None
_detail_cache_at: float = 0.0


async def build_detailed_health_payload(*, service: str) -> dict[str, Any]:
    """Expanded health for monitors and beta ops (cached briefly)."""
    global _detail_cache, _detail_cache_at

    now = time.monotonic()
    if _detail_cache is not None and (now - _detail_cache_at) < 5.0:
        return dict(_detail_cache)

    base = build_health_payload(service=service)
    mongo: dict[str, Any] = {"status": "unknown"}
    try:
        if not (settings.MONGO_URI or "").strip():
            mongo = {"status": "not_configured"}
        else:
            db = get_database()
            await db.command("ping")
            mongo = {"status": "ok"}
    except Exception as exc:
        logger.debug("MongoDB health check failed: %s", exc, exc_info=True)
        mongo = {"status": "down", "error": str(exc)[:120]}

    obs = observability_snapshot()
    overall = base.get("status", "ok")
    if mongo.get("status") != "ok" or not base.get("redis_connected"):
        overall = "degraded"

    payload = {
        **base,
        "status": overall,
        "mongodb": mongo,
        "websocket": {
            "status": "ok",
            "connections": realtime_manager.total_connections(),
        },
        "scan_subsystem": scan_subsystem_summary(),
        "providers": provider_health_from_metrics(),
        "cache_hit_ratio": obs.get("cache_hit_ratio"),
        "extension_min_version": settings.EXTENSION_MIN_VERSION,
        "process_memory": process_memory_snapshot(),
        "feature_flags": {
            "enable_scheduler": settings.ENABLE_SCHEDULER,
            "enable_playwright": settings.ENABLE_PLAYWRIGHT,
            "enable_realtime": settings.ENABLE_REALTIME,
            "enable_automation": settings.ENABLE_AUTOMATION,
            "scheduler_startup_catchup": settings.SCHEDULER_STARTUP_CATCHUP,
        },
    }
    _detail_cache = payload
    _detail_cache_at = now
    return payload
