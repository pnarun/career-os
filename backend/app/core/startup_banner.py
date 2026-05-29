"""Structured startup visibility for Phase 0 stabilization."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.core.runtime_diagnostics import process_memory_snapshot
from app.services.cache_service import is_connected as upstash_connected

logger = logging.getLogger(__name__)


def _playwright_availability() -> str:
    if not settings.ENABLE_PLAYWRIGHT:
        return "disabled_by_config"
    if settings.is_cloud_deploy:
        return "headless_cloud"
    if settings.headed_session_prep_available:
        return "headed_and_headless_local"
    return "headless_local"


def log_startup_banner() -> None:
    """Log service mode and subsystem flags before heavy initialization."""
    mem = process_memory_snapshot()
    mem_line = (
        f"rss_mb={mem.get('rss_mb')} system_mem_pct={mem.get('system_memory_percent')}"
        if mem.get("available")
        else "memory_metrics_unavailable"
    )

    lines = [
        f"[STARTUP] SERVICE_MODE={settings.SERVICE_MODE}",
        f"[STARTUP] ENVIRONMENT={settings.ENVIRONMENT}",
        f"[STARTUP] ENABLE_SCHEDULER={settings.ENABLE_SCHEDULER}",
        f"[STARTUP] SCHEDULER_STARTUP_CATCHUP={settings.SCHEDULER_STARTUP_CATCHUP}",
        f"[STARTUP] ENABLE_REALTIME={settings.ENABLE_REALTIME}",
        f"[STARTUP] ENABLE_AUTOMATION={settings.ENABLE_AUTOMATION}",
        f"[STARTUP] ENABLE_PLAYWRIGHT={settings.ENABLE_PLAYWRIGHT}",
        f"[STARTUP] SCAN_EXECUTION_MODE={settings.SCAN_EXECUTION_MODE}",
        f"[STARTUP] PLAYWRIGHT_AVAILABILITY={_playwright_availability()}",
        f"[STARTUP] REDIS_ENABLED={settings.REDIS_ENABLED}",
        f"[STARTUP] CELERY_ENABLED={settings.CELERY_ENABLED}",
        f"[STARTUP] QUEUE_SCANS_ENABLED={settings.QUEUE_SCANS_ENABLED}",
        f"[STARTUP] UPSTASH_CACHE={'connected' if upstash_connected() else 'not_configured_or_down'}",
        f"[STARTUP] PROCESS_MEMORY {mem_line}",
    ]
    for line in lines:
        logger.info(line, extra={"event": "startup_banner"})
