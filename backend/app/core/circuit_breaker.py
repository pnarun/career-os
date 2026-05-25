"""Provider circuit breaker — temporary cooldown after repeated failures."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

_MEMORY_STATE: dict[str, tuple[int, float]] = {}


def _key(provider: str) -> str:
    return f"circuit:{provider.lower()}"


def record_provider_failure(
    provider: str,
    *,
    threshold: int = 5,
    cooldown_seconds: int = 900,
) -> bool:
    """
    Record a failure. Returns True if circuit is now open (provider disabled).
    """
    now = time.time()
    redis_client = get_redis()
    if redis_client:
        try:
            count = int(redis_client.incr(_key(provider)))
            if count == 1:
                redis_client.expire(_key(provider), cooldown_seconds)
            if count >= threshold:
                redis_client.setex(
                    f"{_key(provider)}:open",
                    cooldown_seconds,
                    "1",
                )
                logger.warning(
                    "Circuit open for provider=%s failures=%d",
                    provider,
                    count,
                    extra={"provider": provider, "event": "circuit_open", "status": "failed"},
                )
                return True
            return False
        except Exception:
            pass

    count, expires = _MEMORY_STATE.get(provider, (0, now + cooldown_seconds))
    if now > expires:
        count = 0
        expires = now + cooldown_seconds
    count += 1
    _MEMORY_STATE[provider] = (count, expires)
    if count >= threshold:
        _MEMORY_STATE[f"{provider}:open"] = (count, now + cooldown_seconds)
        logger.warning(
            "Circuit open for provider=%s failures=%d",
            provider,
            count,
            extra={"provider": provider, "event": "circuit_open", "status": "failed"},
        )
        return True
    return False


def record_provider_success(provider: str) -> None:
    redis_client = get_redis()
    if redis_client:
        try:
            redis_client.delete(_key(provider), f"{_key(provider)}:open")
            return
        except Exception:
            pass
    _MEMORY_STATE.pop(provider, None)
    _MEMORY_STATE.pop(f"{provider}:open", None)


def is_provider_circuit_open(provider: str) -> bool:
    redis_client = get_redis()
    if redis_client:
        try:
            return bool(redis_client.get(f"{_key(provider)}:open"))
        except Exception:
            pass

    entry = _MEMORY_STATE.get(f"{provider}:open")
    if not entry:
        return False
    _, expires = entry
    if time.time() > expires:
        _MEMORY_STATE.pop(f"{provider}:open", None)
        return False
    return True


def circuit_breaker_status() -> dict[str, Any]:
    redis_client = get_redis()
    open_providers: list[str] = []
    if redis_client:
        try:
            for key in redis_client.scan_iter(match="circuit:*:open"):
                provider = key.split(":")[1]
                open_providers.append(provider)
        except Exception:
            pass
    for key in _MEMORY_STATE:
        if key.endswith(":open") and is_provider_circuit_open(key.replace(":open", "")):
            provider = key.replace(":open", "")
            if provider not in open_providers:
                open_providers.append(provider)
    return {"open_providers": sorted(open_providers)}
