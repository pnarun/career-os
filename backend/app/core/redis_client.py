"""Redis client singleton for cache, queues, rate limits, and pub/sub."""

from __future__ import annotations

import logging
from typing import Any

import redis
from redis import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Redis | None = None
_connect_failed: bool = False


def get_redis() -> Redis | None:
    """Return shared Redis client; None when Redis is unavailable."""
    global _client, _connect_failed

    if not settings.REDIS_ENABLED:
        return None

    if _connect_failed:
        return None

    if _client is None:
        try:
            _client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
                health_check_interval=30,
            )
            _client.ping()
            logger.info("Redis connected", extra={"event": "redis_connected"})
        except Exception as exc:
            _connect_failed = True
            _client = None
            logger.warning(
                "Redis unavailable: %s",
                exc,
                extra={"event": "redis_unavailable", "status": "degraded"},
            )
    return _client


def redis_health() -> dict[str, Any]:
    if not settings.REDIS_ENABLED:
        return {"status": "disabled"}
    client = get_redis()
    if client is None:
        return {"status": "down"}
    try:
        client.ping()
        return {"status": "ok", "latency_ms": 0}
    except Exception as exc:
        return {"status": "down", "error": str(exc)}


def close_redis() -> None:
    global _client, _connect_failed
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None
    _connect_failed = False
