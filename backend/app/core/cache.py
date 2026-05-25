"""Redis-backed cache layer with graceful in-memory fallback."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

_memory_cache: dict[str, tuple[float, str]] = {}


def cache_get(key: str) -> Any | None:
    redis_client = get_redis()
    if redis_client:
        try:
            raw = redis_client.get(f"cache:{key}")
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.debug("cache_get redis miss: %s", exc)

    entry = _memory_cache.get(key)
    if not entry:
        return None
    expires_at, raw = entry
    if time.time() > expires_at:
        _memory_cache.pop(key, None)
        return None
    return json.loads(raw)


def cache_set(key: str, value: Any, *, ttl_seconds: int = 300) -> None:
    raw = json.dumps(value, default=str)
    redis_client = get_redis()
    if redis_client:
        try:
            redis_client.setex(f"cache:{key}", ttl_seconds, raw)
            return
        except Exception as exc:
            logger.debug("cache_set redis fallback: %s", exc)

    _memory_cache[key] = (time.time() + ttl_seconds, raw)


def cache_delete(key: str) -> None:
    redis_client = get_redis()
    if redis_client:
        try:
            redis_client.delete(f"cache:{key}")
        except Exception:
            pass
    _memory_cache.pop(key, None)


def cache_key(*parts: str) -> str:
    return ":".join(p.strip() for p in parts if p)
