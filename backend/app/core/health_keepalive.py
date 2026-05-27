"""Ultra-light /health payload for UptimeRobot and frontend keep-alive pings."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

_cache: dict[str, Any] | None = None
_cache_at: float = 0.0


def build_health_payload(
    *,
    service: str,
    version: str,
    environment: str,
) -> dict[str, Any]:
    """No DB, no auth, no scans — scheduler metadata only."""
    from app.services.scheduler_service import get_scheduler_health_snapshot

    snap = get_scheduler_health_snapshot()
    scheduler_state = snap.get("scheduler", "unknown")

    return {
        "status": "ok",
        "service": service,
        "version": version,
        "environment": environment,
        "scheduler": scheduler_state,
        "scheduler_running": bool(snap.get("running")),
        "active_jobs": int(snap.get("active_jobs", 0)),
        "preference_scan_jobs": int(snap.get("preference_scan_jobs", 0)),
        "next_scheduled": snap.get("next_runs", [])[:5],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_cached_health_payload(
    *,
    service: str,
    version: str,
    environment: str,
    ttl_seconds: float = 2.0,
) -> dict[str, Any]:
    global _cache, _cache_at

    now = time.monotonic()
    if _cache is not None and (now - _cache_at) < ttl_seconds:
        cached = dict(_cache)
        cached["timestamp"] = datetime.now(timezone.utc).isoformat()
        cached["cached"] = True
        return cached

    payload = build_health_payload(
        service=service,
        version=version,
        environment=environment,
    )
    _cache = payload
    _cache_at = now
    return payload
