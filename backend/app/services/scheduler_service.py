import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.models.user_preferences import UserPreferencesDocument
from app.services.scan_runner_service import ScanRunnerError, run_scan_for_user
from app.services.user_preferences_service import (
    UserPreferencesServiceError,
    get_active_preferences,
    get_preferences_by_id,
)

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_running_scans: set[str] = set()


def _job_id(preference_id: str) -> str:
    return f"scheduled_scan_{preference_id}"


def _parse_scan_time(scan_time: str) -> tuple[int, int]:
    hour_str, minute_str = scan_time.split(":")
    return int(hour_str), int(minute_str)


def _resolve_timezone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or "Asia/Kolkata")
    except ZoneInfoNotFoundError as exc:
        logger.warning("Unknown timezone %s, falling back to Asia/Kolkata", tz_name)
        return ZoneInfo("Asia/Kolkata")


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


async def _execute_scheduled_scan(preference_id: str) -> None:
    """Run scan for one preference; guard against overlapping runs."""
    if preference_id in _running_scans:
        logger.warning(
            "[SCHEDULED_SCAN_SKIPPED] preference_id=%s reason=already_running",
            preference_id,
        )
        return

    _running_scans.add(preference_id)
    try:
        preferences = await get_preferences_by_id(preference_id)
        if not preferences.is_active:
            logger.info(
                "[SCHEDULED_SCAN_SKIPPED] preference_id=%s reason=inactive",
                preference_id,
            )
            return
        await run_scan_for_user(preferences)
    except (ScanRunnerError, UserPreferencesServiceError) as exc:
        logger.error(
            "[SCHEDULED_SCAN_FAILED] preference_id=%s error=%s",
            preference_id,
            exc,
        )
    finally:
        _running_scans.discard(preference_id)


def register_preference_job(preferences: UserPreferencesDocument) -> None:
    """Register or replace a daily cron job for one preference."""
    scheduler = get_scheduler()
    job_id = _job_id(preferences.id)

    if not preferences.is_active:
        unregister_preference_job(preferences.id)
        return

    hour, minute = _parse_scan_time(preferences.scan_time)
    tz = _resolve_timezone(preferences.timezone)

    trigger = CronTrigger(
        hour=hour,
        minute=minute,
        timezone=tz,
    )

    scheduler.add_job(
        _execute_scheduled_scan,
        trigger=trigger,
        args=[preferences.id],
        id=job_id,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    logger.info(
        "Scheduled daily scan registered: id=%s email=%s at %s %s",
        preferences.id,
        preferences.email,
        preferences.scan_time,
        preferences.timezone,
    )


def unregister_preference_job(preference_id: str) -> None:
    scheduler = get_scheduler()
    job_id = _job_id(preference_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("Scheduled scan removed: preference_id=%s", preference_id)


async def reload_active_schedules() -> int:
    """Load all active preferences and sync scheduler jobs."""
    preferences_list = await get_active_preferences()
    scheduler = get_scheduler()
    active_ids = {pref.id for pref in preferences_list}

    for job in scheduler.get_jobs():
        if job.id.startswith("scheduled_scan_"):
            pref_id = job.id.replace("scheduled_scan_", "", 1)
            if pref_id not in active_ids:
                scheduler.remove_job(job.id)

    for preferences in preferences_list:
        register_preference_job(preferences)

    logger.info("Scheduler synced: %d active preference jobs", len(preferences_list))
    return len(preferences_list)


async def start_scheduler() -> None:
    """Start APScheduler and register active preference jobs."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")
    await reload_active_schedules()


async def shutdown_scheduler() -> None:
    """Gracefully stop background scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
    _scheduler = None
    _running_scans.clear()


async def sync_preference_schedule(preferences: UserPreferencesDocument) -> None:
    """Call after create/update to refresh a single scheduled job."""
    if not get_scheduler().running:
        await start_scheduler()
        return
    register_preference_job(preferences)
