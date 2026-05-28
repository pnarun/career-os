"""Lightweight operational snapshot for beta monitoring."""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.core.metrics import metrics
from app.core.redis_client import get_redis
from app.observability.operational_metrics import observability_snapshot
from app.realtime.websocket_manager import realtime_manager
from app.services.scan_state_service import _is_stale_inflight, _load


def _scan_keys_sample(*, limit: int = 30) -> list[str]:
    client = get_redis()
    if client is None:
        return []
    keys: list[str] = []
    try:
        for key in client.scan_iter(match="scan:state:*", count=50):
            keys.append(key)
            if len(keys) >= limit:
                break
    except Exception:
        return []
    return keys


def scan_subsystem_summary() -> dict[str, Any]:
    """Summarize in-flight scans from Redis (bounded sample)."""
    active = 0
    stuck = 0
    failed_recent = 0
    items: list[dict[str, Any]] = []

    for key in _scan_keys_sample():
        scan_id = key.split(":")[-1] if ":" in key else key
        state = _load(scan_id)
        if state is None:
            continue
        if state.status in ("completed", "failed"):
            if state.status == "failed":
                failed_recent += 1
            continue
        active += 1
        is_stuck = _is_stale_inflight(state)
        if is_stuck:
            stuck += 1
        items.append(
            {
                "scan_id": state.scan_id,
                "user_id": state.user_id[:8] + "…" if state.user_id else "",
                "status": state.status,
                "progress": state.progress,
                "stuck": is_stuck,
                "started_at": state.started_at,
            }
        )

    return {
        "active_inflight": active,
        "stuck_estimate": stuck,
        "failed_in_sample": failed_recent,
        "sample": items[:15],
        "stale_threshold_seconds": settings.SCAN_STALE_SECONDS,
    }


def provider_health_from_metrics() -> dict[str, Any]:
    snap = metrics.snapshot()
    failures = int(snap.get("provider_failure_total", 0) or 0)
    success = int(snap.get("provider_success_total", 0) or 0)
    total = failures + success
    return {
        "fetch_success": success,
        "fetch_failures": failures,
        "failure_rate": round(failures / total, 3) if total else None,
        "last_durations_ms": {
            k.replace("provider_", "").replace("_last_duration_ms", ""): v
            for k, v in snap.items()
            if k.endswith("_last_duration_ms")
        },
    }


async def beta_ops_snapshot() -> dict[str, Any]:
    obs = observability_snapshot()
    return {
        "environment": settings.ENVIRONMENT,
        "websocket_connections": realtime_manager.total_connections(),
        "cache_hit_ratio": obs.get("cache_hit_ratio"),
        "scan_subsystem": scan_subsystem_summary(),
        "providers": provider_health_from_metrics(),
        "metrics": {
            "scans_total": obs.get("scans_total"),
            "api_slow_total": obs.get("api_slow_total"),
            "rate_limit_blocked": obs.get("rate_limit_blocked"),
        },
        "extension_min_version": settings.EXTENSION_MIN_VERSION,
    }
