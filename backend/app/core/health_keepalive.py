"""Ultra-light /health payload for UptimeRobot and frontend keep-alive pings."""

from __future__ import annotations

import logging
import time
from typing import Any

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


def build_health_payload(*, service: str) -> dict[str, Any]:
    """No DB, no auth, no scans — minimal fields for keep-alive."""
    return {
        "status": "ok",
        "service": service,
        "scheduler": _scheduler_status(),
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
