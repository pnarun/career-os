"""Shared process bootstrap (Mongo, Redis, cache, indexes)."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo
from app.core.redis_client import close_redis, get_redis
from app.core.startup_banner import log_startup_banner
from app.core.startup_checks import log_startup_verification
from app.db.indexes import ensure_all_mongo_indexes
from app.runtime.service_mode import runtime
from app.services.automation_service import shutdown_automation
from app.services.migration_service import run_legacy_data_migration, seed_demo_users
from app.services.scheduler_service import shutdown_scheduler, start_scheduler

logger = logging.getLogger(__name__)


async def bootstrap_core(*, run_migrations: bool = True) -> None:
    """Initialize shared infrastructure for any runtime mode."""
    log_startup_banner()
    logger.info(
        "[STARTUP] Runtime profile=%s",
        runtime.profile_summary(),
        extra={"event": "startup", "runtime": runtime.profile_summary()},
    )
    await connect_to_mongo()
    get_redis()
    from app.services.cache_service import init_upstash_cache

    init_upstash_cache()
    await ensure_all_mongo_indexes()
    if run_migrations:
        await run_legacy_data_migration()
        await seed_demo_users()


async def bootstrap_api_subsystems() -> object | None:
    """Start API-specific subsystems; returns realtime asyncio task if any."""
    realtime_task = None
    if runtime.should_start_scheduler():
        logger.info(
            "[STARTUP] Scheduler owner=%s (mode=%s)",
            runtime.scheduler_owner_label(),
            runtime.mode.value,
            extra={"event": "startup", "scheduler_owner": runtime.scheduler_owner_label()},
        )
        await start_scheduler()
    else:
        logger.info(
            "[STARTUP] Scheduler not started owner=%s mode=%s ENABLE_SCHEDULER=%s",
            runtime.scheduler_owner_label(),
            runtime.mode.value,
            settings.ENABLE_SCHEDULER,
            extra={"event": "startup", "scheduler": "disabled", "scheduler_owner": "none"},
        )

    if runtime.should_start_realtime():
        from app.realtime.redis_bridge import start_realtime_subscriber

        realtime_task = await start_realtime_subscriber()
        logger.info(
            "[STARTUP] Realtime subscriber state=%s",
            "started" if realtime_task else "in_process_only",
            extra={"event": "startup", "realtime": "enabled"},
        )
    else:
        logger.info(
            "[STARTUP] Realtime not started (mode=%s)",
            runtime.mode.value,
            extra={"event": "startup", "realtime": "disabled"},
        )

    await log_startup_verification()
    return realtime_task


async def bootstrap_scan_worker_subsystems() -> None:
    """Scan worker: scheduler + no HTTP/realtime."""
    if runtime.should_start_scheduler():
        logger.info(
            "[STARTUP] Scheduler owner=%s — scan worker owns APScheduler",
            runtime.scheduler_owner_label(),
            extra={"event": "startup", "scheduler_owner": runtime.scheduler_owner_label()},
        )
        await start_scheduler()
    else:
        logger.warning(
            "[STARTUP] Scan worker started without scheduler (ENABLE_SCHEDULER=false)",
            extra={"event": "startup", "scheduler": "disabled"},
        )
    await log_startup_verification()


async def bootstrap_automation_worker_subsystems() -> None:
    """Automation worker: Playwright runtime only."""
    await log_startup_verification()


async def shutdown_api_subsystems(realtime_task: object | None) -> None:
    if realtime_task is not None:
        realtime_task.cancel()  # type: ignore[attr-defined]
    if runtime.should_start_scheduler():
        await shutdown_scheduler()
    if runtime.should_start_automation_shutdown():
        await shutdown_automation()
    close_redis()
    await close_mongo_connection()


async def shutdown_worker_subsystems() -> None:
    if runtime.should_start_scheduler():
        await shutdown_scheduler()
    if runtime.should_start_automation_shutdown():
        await shutdown_automation()
    close_redis()
    await close_mongo_connection()
