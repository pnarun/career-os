"""Centralized in-process metrics and structured operational logging."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.metrics import metrics

logger = logging.getLogger(__name__)

_cache_hits = 0
_cache_misses = 0
_last_ratio_log_at = 0.0


def _maybe_log_cache_ratio() -> None:
    global _last_ratio_log_at
    total = _cache_hits + _cache_misses
    if total < 20 or total % 50 != 0:
        return
    now = time.time()
    if now - _last_ratio_log_at < 120:
        return
    _last_ratio_log_at = now
    ratio = round(_cache_hits / total, 3) if total else 0.0
    logger.info(
        "CACHE_HIT_RATIO hits=%d misses=%d ratio=%s",
        _cache_hits,
        _cache_misses,
        ratio,
        extra={
            "event": "CACHE_HIT_RATIO",
            "cache_hits": _cache_hits,
            "cache_misses": _cache_misses,
            "hit_ratio": ratio,
        },
    )
    metrics.set_gauge("cache_hit_ratio", ratio)


def record_cache_hit() -> None:
    global _cache_hits
    _cache_hits += 1
    metrics.incr("cache_hits")
    _maybe_log_cache_ratio()


def record_cache_miss() -> None:
    global _cache_misses
    _cache_misses += 1
    metrics.incr("cache_misses")
    _maybe_log_cache_ratio()


def record_api_latency(path: str, method: str, duration_ms: float, status_code: int) -> None:
    metrics.incr("api_requests_total")
    metrics.incr(f"api_status_{status_code // 100}xx")
    if duration_ms >= 2000:
        metrics.incr("api_slow_total")
    key = f"api_latency_ms:{method}:{path}"
    metrics.set_gauge(key, round(duration_ms, 1))


def record_provider_fetch(
    provider: str,
    *,
    duration_ms: int,
    success: bool,
    error_type: str = "",
) -> None:
    metrics.incr("provider_fetches_total")
    metrics.incr(f"provider_{provider}_fetches")
    if success:
        metrics.incr("provider_success_total")
        metrics.incr(f"provider_{provider}_success")
    else:
        metrics.incr("provider_failure_total")
        metrics.incr(f"provider_{provider}_failure")
    metrics.set_gauge(f"provider_{provider}_last_duration_ms", float(duration_ms))
    if not success and error_type == "timeout":
        logger.warning(
            "PROVIDER_TIMEOUT provider=%s duration_ms=%d",
            provider,
            duration_ms,
            extra={
                "event": "PROVIDER_TIMEOUT",
                "provider": provider,
                "duration_ms": duration_ms,
            },
        )


def record_scan_duration(scan_id: str, duration_ms: float, *, status: str) -> None:
    metrics.incr("scans_total")
    metrics.incr(f"scans_{status}")
    metrics.set_gauge("scan_last_duration_ms", duration_ms)
    logger.info(
        "SCAN_DURATION scan_id=%s status=%s duration_ms=%.0f",
        scan_id,
        status,
        duration_ms,
        extra={
            "event": "scan_duration",
            "scan_id": scan_id,
            "status": status,
            "duration_ms": duration_ms,
        },
    )


def record_mongo_aggregation(name: str, duration_ms: float) -> None:
    metrics.incr("mongo_aggregations_total")
    metrics.set_gauge(f"mongo_agg_{name}_last_ms", duration_ms)


def record_websocket_connected(user_id: str, total_for_user: int) -> None:
    metrics.incr("websocket_connections_total")
    metrics.set_gauge("websocket_active_connections", float(total_for_user))
    logger.info(
        "WEBSOCKET_CONNECTED user_id=%s connections=%d",
        user_id,
        total_for_user,
        extra={
            "event": "WEBSOCKET_CONNECTED",
            "user_id": user_id,
            "connections": total_for_user,
        },
    )


def record_websocket_disconnected(user_id: str) -> None:
    metrics.incr("websocket_disconnections_total")
    logger.info(
        "WEBSOCKET_DISCONNECTED user_id=%s",
        user_id,
        extra={"event": "WEBSOCKET_DISCONNECTED", "user_id": user_id},
    )


def observability_snapshot() -> dict[str, Any]:
    snap = metrics.snapshot()
    total = _cache_hits + _cache_misses
    snap["cache_hit_ratio"] = round(_cache_hits / total, 3) if total else None
    return snap
