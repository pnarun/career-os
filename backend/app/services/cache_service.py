"""Upstash Redis REST cache layer with in-memory fallback."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.config import settings
from app.observability.operational_metrics import record_cache_hit, record_cache_miss

logger = logging.getLogger(__name__)

_client: Any | None = None
_client_checked: bool = False
_client_connected: bool = False
_memory_cache: dict[str, tuple[float, str]] = {}


def _cache_enabled() -> bool:
    return bool(
        (settings.UPSTASH_REDIS_REST_URL or "").strip()
        and (settings.UPSTASH_REDIS_REST_TOKEN or "").strip()
    )


def _get_client() -> Any | None:
    """Lazy Upstash Redis REST client; None when unavailable or misconfigured."""
    global _client, _client_checked, _client_connected

    if not _cache_enabled():
        _client_checked = True
        _client_connected = False
        return None

    if _client_checked:
        return _client

    _client_checked = True
    try:
        from upstash_redis import Redis

        _client = Redis(
            url=settings.UPSTASH_REDIS_REST_URL.strip(),
            token=settings.UPSTASH_REDIS_REST_TOKEN.strip(),
        )
        _client.ping()
        _client_connected = True
        logger.info(
            "Upstash Redis cache connected",
            extra={"event": "upstash_cache_connected"},
        )
    except Exception as exc:
        _client = None
        _client_connected = False
        logger.warning(
            "Upstash Redis unavailable — using in-memory cache fallback: %s",
            exc,
            extra={"event": "upstash_cache_unavailable"},
        )
    return _client


def init_upstash_cache() -> None:
    """Warm Upstash client on application startup."""
    _get_client()


def is_connected() -> bool:
    """True when Upstash Redis REST ping succeeded."""
    if not _cache_enabled():
        return False
    _get_client()
    return _client_connected


def _memory_get(key: str) -> Any | None:
    entry = _memory_cache.get(key)
    if not entry:
        return None
    expires_at, raw = entry
    if time.time() > expires_at:
        _memory_cache.pop(key, None)
        return None
    return json.loads(raw)


def _memory_set(key: str, value: Any, ttl_seconds: int) -> None:
    _memory_cache[key] = (time.time() + ttl_seconds, json.dumps(value, default=str))


def _memory_delete(key: str) -> None:
    _memory_cache.pop(key, None)


def _memory_exists(key: str) -> bool:
    entry = _memory_cache.get(key)
    if not entry:
        return False
    expires_at, _ = entry
    if time.time() > expires_at:
        _memory_cache.pop(key, None)
        return False
    return True


def get_json(key: str) -> Any | None:
    client = _get_client()
    if client is not None:
        try:
            raw = client.get(key)
            if raw is None:
                record_cache_miss()
                logger.info(
                    "CACHE MISS key=%s",
                    key,
                    extra={"event": "cache_miss", "cache_key": key},
                )
                return None
            record_cache_hit()
            logger.info(
                "CACHE HIT key=%s",
                key,
                extra={"event": "cache_hit", "cache_key": key},
            )
            if isinstance(raw, (dict, list)):
                return raw
            return json.loads(raw)
        except Exception as exc:
            logger.debug("Upstash get_json failed key=%s: %s", key, exc)

    value = _memory_get(key)
    if value is not None:
        record_cache_hit()
        logger.info(
            "CACHE HIT (memory) key=%s",
            key,
            extra={"event": "cache_hit", "cache_key": key, "backend": "memory"},
        )
    else:
        record_cache_miss()
        logger.info(
            "CACHE MISS (memory) key=%s",
            key,
            extra={"event": "cache_miss", "cache_key": key, "backend": "memory"},
        )
    return value


def set_json(key: str, value: Any, ttl_seconds: int) -> None:
    raw = json.dumps(value, default=str)
    client = _get_client()
    if client is not None:
        try:
            client.set(key, raw, ex=ttl_seconds)
            logger.info(
                "CACHE SET key=%s ttl=%ss",
                key,
                ttl_seconds,
                extra={"event": "cache_set", "cache_key": key, "ttl_seconds": ttl_seconds},
            )
            return
        except Exception as exc:
            logger.debug("Upstash set_json failed key=%s: %s", key, exc)

    _memory_set(key, value, ttl_seconds)
    logger.info(
        "CACHE SET (memory) key=%s ttl=%ss",
        key,
        ttl_seconds,
        extra={
            "event": "cache_set",
            "cache_key": key,
            "ttl_seconds": ttl_seconds,
            "backend": "memory",
        },
    )


def delete(key: str) -> None:
    client = _get_client()
    if client is not None:
        try:
            client.delete(key)
        except Exception as exc:
            logger.debug("Upstash delete failed key=%s: %s", key, exc)
    _memory_delete(key)


def exists(key: str) -> bool:
    client = _get_client()
    if client is not None:
        try:
            result = client.exists(key)
            return bool(result)
        except Exception as exc:
            logger.debug("Upstash exists failed key=%s: %s", key, exc)
    return _memory_exists(key)


def delete_by_prefix(prefix: str) -> int:
    """Delete keys matching prefix (best-effort; safe no-op on failure)."""
    removed = 0
    client = _get_client()
    if client is not None:
        try:
            keys = client.keys(f"{prefix}*")
            if keys:
                if isinstance(keys, list):
                    client.delete(*keys)
                    removed = len(keys)
                else:
                    client.delete(keys)
                    removed = 1
        except Exception as exc:
            logger.debug("Upstash delete_by_prefix failed prefix=%s: %s", prefix, exc)

    stale = [k for k in list(_memory_cache.keys()) if k.startswith(prefix)]
    for key in stale:
        _memory_delete(key)
        removed += 1
    if removed:
        logger.info(
            "CACHE DELETE prefix=%s count=%s",
            prefix,
            removed,
            extra={"event": "cache_invalidate", "prefix": prefix, "count": removed},
        )
    return removed


def invalidate_user_caches(user_id: str) -> None:
    """Drop cached dashboard/analytics/scan/jobs payloads for a user."""
    if not user_id:
        return
    from app.utils.cache_keys import user_cache_prefixes

    for prefix in user_cache_prefixes(user_id):
        delete_by_prefix(prefix)
