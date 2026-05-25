"""Session prepare logs — visible in worker stderr and parent API process."""

from __future__ import annotations

import logging
import sys
import traceback

_SESSION_LOGGER = logging.getLogger("app.automation.session")


def configure_session_logging() -> None:
    """Ensure worker subprocess emits INFO logs to stderr."""
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s:%(name)s:%(message)s",
            stream=sys.stderr,
            force=True,
        )
    _SESSION_LOGGER.setLevel(logging.INFO)
    for handler in logging.getLogger().handlers:
        if hasattr(handler, "flush"):
            handler.flush()


def session_log(message: str) -> None:
    """Log to stderr (flushed immediately for streaming worker output)."""
    _SESSION_LOGGER.info(message)
    print(message, file=sys.stderr, flush=True)
    sys.stderr.flush()


def session_log_traceback(context: str) -> None:
    """Emit full traceback to stderr (no silent failures)."""
    tb = traceback.format_exc()
    session_log(f"[SESSION] TRACEBACK ({context}):\n{tb}")


def worker_log(message: str) -> None:
    """Worker subprocess dispatch layer (always flushed)."""
    session_log(f"[WORKER] {message}")
