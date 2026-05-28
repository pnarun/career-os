"""Startup verification — log dependency readiness without blocking boot."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.core.database import get_database
from app.core.redis_client import get_redis, redis_health
from app.realtime.websocket_manager import realtime_manager

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

    redis = redis_health()
    redis_status = redis.get("status", "unknown")

    logger.info(
        "Startup verification environment=%s mongo=%s redis=%s websocket=ready "
        "extension_min_version=%s scheduler_heartbeat=%s",
        settings.ENVIRONMENT,
        mongo_status,
        redis_status,
        settings.EXTENSION_MIN_VERSION,
        settings.SCHEDULER_HEARTBEAT_ENABLED,
        extra={
            "event": "startup_verification",
            "mongo_status": mongo_status,
            "redis_status": redis_status,
            "websocket_connections": realtime_manager.total_connections(),
            "extension_min_version": settings.EXTENSION_MIN_VERSION,
        },
    )

    if mongo_status == "down":
        logger.warning("MongoDB ping failed on startup: %s", mongo_error or "unknown")
    if settings.REDIS_ENABLED and redis_status == "down":
        logger.warning("Redis unavailable on startup — cache and rate limits may degrade")

    client = get_redis()
    if settings.REDIS_ENABLED and client is None and redis_status != "disabled":
        logger.warning("Redis client not initialized — check REDIS_URL")
