"""Startup verification — log dependency readiness without blocking boot."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.core.database import get_database
from app.core.redis_client import get_redis, redis_health
from app.core.runtime_diagnostics import process_memory_snapshot
from app.core.storage_report import log_storage_report
from app.realtime.websocket_manager import realtime_manager
from app.runtime.service_mode import runtime
from app.services.scheduler_service import get_scheduler_health_snapshot

logger = logging.getLogger(__name__)


async def log_startup_verification() -> None:
    """Ping Mongo/Redis and log subsystem readiness for beta ops."""
    mongo_status = "unknown"
    mongo_error = ""
    try:
        if not (settings.MONGO_URI or "").strip():
            mongo_status = "not_configured"
        else:
            db = get_database()
            await db.command("ping")
            mongo_status = "ok"
    except Exception as exc:
        mongo_status = "down"
        mongo_error = str(exc)[:200]
        logger.exception(
            "MongoDB ping failed on startup",
            extra={"event": "startup_verification", "mongo_status": mongo_status},
        )

    redis = redis_health()
    redis_status = redis.get("status", "unknown")
    scheduler_snap = get_scheduler_health_snapshot()
    memory = process_memory_snapshot()

    logger.info(
        "[STARTUP] verification complete environment=%s mongo=%s redis=%s "
        "scheduler=%s realtime=%s automation=%s celery=%s memory_rss_mb=%s",
        settings.ENVIRONMENT,
        mongo_status,
        redis_status,
        scheduler_snap.get("scheduler", "unknown"),
        "enabled" if settings.ENABLE_REALTIME else "disabled",
        "enabled" if settings.ENABLE_AUTOMATION else "disabled",
        "enabled" if settings.CELERY_ENABLED else "disabled",
        memory.get("rss_mb") if memory.get("available") else "n/a",
        extra={
            "event": "startup_verification",
            "mongo_status": mongo_status,
            "redis_status": redis_status,
            "scheduler": scheduler_snap,
            "websocket_connections": realtime_manager.total_connections(),
            "extension_min_version": settings.EXTENSION_MIN_VERSION,
            "scheduler_startup_catchup": settings.SCHEDULER_STARTUP_CATCHUP,
            "enable_scheduler": settings.ENABLE_SCHEDULER,
            "enable_playwright": settings.ENABLE_PLAYWRIGHT,
            "enable_realtime": settings.ENABLE_REALTIME,
            "enable_automation": settings.ENABLE_AUTOMATION,
            "service_mode": settings.SERVICE_MODE,
            "realtime_bridge": runtime.should_start_realtime_bridge(),
            "scan_execution_mode": settings.SCAN_EXECUTION_MODE,
            "process_memory": memory,
        },
    )

    if mongo_status == "down":
        logger.warning("MongoDB ping failed on startup: %s", mongo_error or "unknown")
    if settings.REDIS_ENABLED and redis_status == "down":
        logger.warning("Redis unavailable on startup — cache and rate limits may degrade")

    client = get_redis()
    if settings.REDIS_ENABLED and client is None and redis_status != "disabled":
        logger.warning("Redis client not initialized — check REDIS_URL")

    await log_storage_report()
