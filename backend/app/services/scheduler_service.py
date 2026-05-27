import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.automation.job_scan_automation_service import (
    run_daily_job_scan_automation,
    run_follow_up_reminders,
    run_interview_reminders,
    run_weekly_career_insights,
)
from app.models.user_preferences import UserPreferencesDocument
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


def get_scheduler_health_snapshot() -> dict[str, Any]:
    """Lightweight scheduler metadata for /health (no DB, no job execution)."""
    scheduler = _scheduler
    if scheduler is None or not scheduler.running:
        return {
            "scheduler": "stopped",
            "running": False,
            "active_jobs": 0,
            "preference_scan_jobs": 0,
            "next_runs": [],
        }

    jobs = scheduler.get_jobs()
    preference_jobs = [j for j in jobs if j.id.startswith("scheduled_scan_")]
    next_runs: list[dict[str, str]] = []

    def _sort_key(job) -> datetime:
        nrt = job.next_run_time
        if nrt is None:
            return datetime.max.replace(tzinfo=timezone.utc)
        if nrt.tzinfo is None:
            return nrt.replace(tzinfo=timezone.utc)
        return nrt

    for job in sorted(jobs, key=_sort_key)[:8]:
        if job.next_run_time is None:
            continue
        next_runs.append(
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat(),
            }
        )

    return {
        "scheduler": "running",
        "running": True,
        "active_jobs": len(jobs),
        "preference_scan_jobs": len(preference_jobs),
        "next_runs": next_runs,
    }


def log_scheduler_startup_summary() -> None:
    snap = get_scheduler_health_snapshot()
    logger.info("[SCHEDULER] Initialized")
    logger.info("[SCHEDULER] Active jobs: %s", snap.get("active_jobs", 0))
    logger.info(
        "[SCHEDULER] Preference scan jobs: %s",
        snap.get("preference_scan_jobs", 0),
    )
    for entry in snap.get("next_runs", [])[:5]:
        logger.info(
            "[SCHEDULER] Next %s: %s",
            entry.get("id", "?"),
            entry.get("next_run", "?"),
        )


async def _scheduler_heartbeat() -> None:
    snap = get_scheduler_health_snapshot()
    logger.info(
        "[SCHEDULER] heartbeat alive jobs=%s scans=%s",
        snap.get("active_jobs", 0),
        snap.get("preference_scan_jobs", 0),
    )


def _register_heartbeat_job() -> None:
    from app.core.config import settings

    if not settings.SCHEDULER_HEARTBEAT_ENABLED:
        return
    scheduler = get_scheduler()
    scheduler.add_job(
        _scheduler_heartbeat,
        trigger=IntervalTrigger(minutes=30),
        id="scheduler_heartbeat",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


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
        await run_daily_job_scan_automation(preference_id)
    except UserPreferencesServiceError as exc:
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

    tz = _resolve_timezone(preferences.timezone)
    frequency = (preferences.frequency or "every_6h").strip().lower()
    use_six_hour = frequency == "every_6h" or bool(
        getattr(preferences, "use_default_six_hour_schedule", False)
    )

    if use_six_hour:
        trigger = CronTrigger(
            hour="0,6,12,18",
            minute=0,
            timezone=tz,
        )
        misfire_grace = 6 * 3600
    else:
        hour, minute = _parse_scan_time(preferences.scan_time)
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=tz,
        )
        misfire_grace = 3600

    scheduler.add_job(
        _execute_scheduled_scan,
        trigger=trigger,
        args=[preferences.id],
        id=job_id,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=misfire_grace,
    )

    logger.info(
        "Scheduled scan registered: id=%s email=%s frequency=%s tz=%s six_hour=%s",
        preferences.id,
        preferences.email,
        frequency,
        preferences.timezone,
        use_six_hour,
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


async def _execute_follow_up_reminders() -> None:
    try:
        await run_follow_up_reminders()
    except Exception as exc:
        logger.error("[FOLLOW_UP_REMINDERS_FAILED] error=%s", exc)


async def _execute_interview_reminders() -> None:
    try:
        await run_interview_reminders()
    except Exception as exc:
        logger.error("[INTERVIEW_REMINDERS_FAILED] error=%s", exc)


async def _execute_weekly_insights() -> None:
    try:
        await run_weekly_career_insights()
    except Exception as exc:
        logger.error("[WEEKLY_INSIGHTS_FAILED] error=%s", exc)


def _register_system_jobs() -> None:
    """Register global automation jobs (reminders, weekly insights)."""
    scheduler = get_scheduler()

    scheduler.add_job(
        _execute_follow_up_reminders,
        trigger=CronTrigger(hour=9, minute=0, timezone="UTC"),
        id="follow_up_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _execute_interview_reminders,
        trigger=CronTrigger(hour=8, minute=30, timezone="UTC"),
        id="interview_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _execute_weekly_insights,
        trigger=CronTrigger(day_of_week="sun", hour=10, minute=0, timezone="UTC"),
        id="weekly_career_insights",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info("System automation jobs registered")


def _parse_last_email_sent(raw: str) -> datetime | None:
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None


def _uses_six_hour_schedule(preferences: UserPreferencesDocument) -> bool:
    frequency = (preferences.frequency or "every_6h").strip().lower()
    return frequency == "every_6h" or bool(
        getattr(preferences, "use_default_six_hour_schedule", False)
    )


def _hours_since_last_email(preferences: UserPreferencesDocument, now_utc: datetime) -> float | None:
    last = _parse_last_email_sent(preferences.last_email_sent_at)
    if last is None:
        return None
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (now_utc - last.astimezone(timezone.utc)).total_seconds() / 3600


def is_preference_due_for_scan(
    preferences: UserPreferencesDocument,
    *,
    now_utc: datetime | None = None,
) -> bool:
    """True when a scheduled scan should run (missed slot or never ran)."""
    if not preferences.is_active:
        return False

    now_utc = now_utc or datetime.now(timezone.utc)
    hours = _hours_since_last_email(preferences, now_utc)

    if _uses_six_hour_schedule(preferences):
        if hours is None:
            return True
        if hours >= 5.5:
            return True
        tz = _resolve_timezone(preferences.timezone)
        local = now_utc.astimezone(tz)
        if local.hour in (0, 6, 12, 18) and local.minute < 50 and hours >= 4.0:
            return True
        return False

    frequency = (preferences.frequency or "daily").strip().lower()
    if frequency == "weekly":
        tz = _resolve_timezone(preferences.timezone)
        local = now_utc.astimezone(tz)
        if local.weekday() != 6:
            return False
    if hours is not None and hours < 20:
        return False
    tz = _resolve_timezone(preferences.timezone)
    local = now_utc.astimezone(tz)
    hour, minute = _parse_scan_time(preferences.scan_time or "08:00")
    if local.hour == hour and local.minute < 50:
        return hours is None or hours >= 20
    return hours is None


async def run_overdue_scheduled_scans() -> dict[str, object]:
    """Run scans for active users who missed a slot (e.g. Render was asleep)."""
    preferences_list = await get_active_preferences()
    now_utc = datetime.now(timezone.utc)
    ran: list[str] = []
    skipped: list[str] = []

    for preferences in preferences_list:
        if not is_preference_due_for_scan(preferences, now_utc=now_utc):
            skipped.append(preferences.id)
            continue
        await _execute_scheduled_scan(preferences.id)
        ran.append(preferences.id)

    logger.info(
        "Overdue scheduled scans: ran=%d skipped=%d",
        len(ran),
        len(skipped),
    )
    return {"ran": len(ran), "preference_ids": ran, "skipped": len(skipped)}


async def start_scheduler() -> None:
    """Start APScheduler and register active preference jobs."""
    from app.core.config import settings

    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")
    _register_system_jobs()
    _register_heartbeat_job()
    await reload_active_schedules()
    log_scheduler_startup_summary()

    if settings.SCHEDULER_STARTUP_CATCHUP:
        try:
            catchup = await run_overdue_scheduled_scans()
            logger.info("[SCHEDULER] Startup catch-up: %s", catchup)
        except Exception as exc:
            logger.error("[SCHEDULER] Startup catch-up failed: %s", exc)


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
