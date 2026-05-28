"""Structured JSON logging for production observability."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def __init__(self, service: str = "career-os-api") -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        from app.core.user_context import get_request_user_email

        user_email = (
            getattr(record, "user", None)
            or getattr(record, "user_email", None)
            or get_request_user_email()
        )

        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user_email,
            "service": getattr(record, "service", self.service),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "event": getattr(record, "event", record.funcName or "log"),
        }

        for key in ("provider", "status", "user_id", "scan_id", "task_id", "queue"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class RingBufferHandler(logging.Handler):
    """Keep recent log lines in memory for /logs viewer (demo & ops)."""

    def __init__(self, buffer, level: int = logging.NOTSET) -> None:
        super().__init__(level)
        self._buffer = buffer

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._buffer.append(msg)
        except Exception:
            self.handleError(record)


def configure_logging(*, service: str = "career-os-api", level: str = "INFO") -> None:
    from app.core.log_buffer import log_buffer

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = StructuredFormatter(service=service)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    root.addHandler(stdout_handler)

    ring_handler = RingBufferHandler(log_buffer)
    ring_handler.setFormatter(formatter)
    root.addHandler(ring_handler)

    for name in (
        "urllib3",
        "httpx",
        "httpcore",
        "apscheduler",
        "motor",
        "uvicorn.access",
        "watchfiles",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)

    if level.upper() in ("WARNING", "ERROR", "CRITICAL"):
        logging.getLogger("app").setLevel(getattr(logging, level.upper(), logging.WARNING))


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    **fields: Any,
) -> None:
    """Log with structured extra fields."""
    extra = {"event": event, **fields}
    logger.log(level, message, extra=extra)
