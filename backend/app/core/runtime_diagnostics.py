"""Lightweight process memory/CPU diagnostics (Phase 0 — no external APM)."""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

_psutil_module: Any | None = None
_psutil_checked = False


def _get_psutil():
    """Lazy-load psutil; return None when unavailable."""
    global _psutil_module, _psutil_checked
    if _psutil_checked:
        return _psutil_module
    _psutil_checked = True
    try:
        import psutil as psutil_mod

        _psutil_module = psutil_mod
    except ImportError:
        _psutil_module = None
    return _psutil_module


def process_memory_snapshot() -> dict[str, Any]:
    """
    Current process RSS and optional system metrics.
    Returns ``available: false`` when psutil is not installed.
    """
    psutil = _get_psutil()
    if psutil is None:
        return {"available": False, "reason": "psutil_not_installed"}

    try:
        proc = psutil.Process()
        mem_info = proc.memory_info()
        rss_mb = round(mem_info.rss / (1024 * 1024), 2)
        vms_mb = round(mem_info.vms / (1024 * 1024), 2)
        result: dict[str, Any] = {
            "available": True,
            "rss_mb": rss_mb,
            "vms_mb": vms_mb,
            "threads": threading.active_count(),
            "thread_count": proc.num_threads(),
        }
        try:
            result["system_memory_percent"] = round(psutil.virtual_memory().percent, 1)
        except Exception:
            pass
        try:
            result["cpu_percent"] = round(proc.cpu_percent(interval=None), 1)
        except Exception:
            pass
        return result
    except Exception as exc:
        logger.debug("process_memory_snapshot failed: %s", exc)
        return {"available": False, "reason": str(exc)[:120]}


def log_memory_event(event: str, **extra: Any) -> dict[str, Any]:
    """
    One-shot structured memory log at scan/playwright boundaries.
    Does not poll — call only at operation start/end.
    """
    snap = process_memory_snapshot()
    log_extra: dict[str, Any] = {"event": event, **extra}
    if snap.get("available"):
        log_extra.update(snap)
        logger.info(
            "%s rss_mb=%s system_mem_pct=%s threads=%s",
            event,
            snap.get("rss_mb"),
            snap.get("system_memory_percent"),
            snap.get("thread_count", snap.get("threads")),
            extra=log_extra,
        )
    else:
        logger.info(
            "%s (process memory metrics unavailable: %s)",
            event,
            snap.get("reason", "unknown"),
            extra=log_extra,
        )
    return snap
