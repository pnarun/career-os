"""Redis-backed API rate limiting middleware."""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.metrics import metrics
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

# path prefix -> (limit, window_seconds)
RATE_LIMIT_RULES: dict[str, tuple[int, int]] = {
    "/auth/login": (10, 60),
    "/auth/register": (5, 60),
    "/auth/password-reset/request": (5, 300),
    "/auth/password-reset/confirm": (10, 300),
    "/run-scan-now": (6, 60),
    "/fetch-jobs": (10, 60),
    "/fetch-linkedin": (5, 60),
    "/automation/linkedin/connect-with-code": (8, 300),
    "/automation/linkedin/resync": (20, 60),
    "/automation/linkedin/pairing-code": (6, 300),
    "/scans/run": (6, 60),
}


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return ip


def _match_rule(path: str) -> tuple[str, int, int] | None:
    for prefix, (limit, window) in RATE_LIMIT_RULES.items():
        if path.startswith(prefix) or path.endswith(prefix):
            return prefix, limit, window
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        rule = _match_rule(request.url.path)
        if not rule:
            return await call_next(request)

        prefix, limit, window = rule
        client = _client_key(request)
        redis_key = f"rl:{prefix}:{client}"

        redis_client = get_redis()
        if redis_client:
            try:
                count = redis_client.incr(redis_key)
                if count == 1:
                    redis_client.expire(redis_key, window)
                if count > limit:
                    metrics.incr("rate_limit_blocked")
                    logger.warning(
                        "Rate limit exceeded path=%s client=%s",
                        prefix,
                        client,
                        extra={"event": "rate_limit", "status": "blocked"},
                    )
                    return JSONResponse(
                        status_code=429,
                        content={"detail": {"message": "Rate limit exceeded. Try again later."}},
                    )
            except Exception as exc:
                logger.debug("Rate limit redis error: %s", exc)

        return await call_next(request)
