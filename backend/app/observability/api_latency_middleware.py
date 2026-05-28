"""Log and count slow HTTP API requests."""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.observability.operational_metrics import record_api_latency

logger = logging.getLogger(__name__)

_SKIP_PREFIXES = ("/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico", "/brand/")


class ApiLatencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.scope.get("type") != "http":
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            return await call_next(request)

        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        method = request.method
        status = response.status_code

        record_api_latency(path, method, duration_ms, status)

        threshold = settings.API_SLOW_REQUEST_MS
        if duration_ms >= threshold:
            logger.warning(
                "SLOW_API %s %s status=%s duration_ms=%.1f",
                method,
                path,
                status,
                duration_ms,
                extra={
                    "event": "slow_api",
                    "method": method,
                    "path": path,
                    "status_code": status,
                    "duration_ms": round(duration_ms, 1),
                },
            )

        return response
