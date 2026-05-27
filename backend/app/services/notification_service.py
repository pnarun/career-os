"""In-app and email notification delivery."""

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.models.automation_run import AutomationRunDocument
from app.models.job import JobDocument
from app.models.notification import (
    NotificationCreate,
    NotificationDocument,
    NotificationListResponse,
)
from app.models.user_preferences import UserPreferencesDocument
from app.services.email_service import (
    EmailNotConfiguredError,
    EmailServiceError,
    ScanEmailSummary,
    _dispatch_resend,
    _format_source_label,
    build_no_match_email,
    build_opportunities_email,
)

logger = logging.getLogger(__name__)

NOTIFICATIONS_COLLECTION = "notifications"
AUTOMATION_RUNS_COLLECTION = "automation_runs"
HIGH_MATCH_THRESHOLD = 85

def _utc_now_iso() -> str:
    """Small shared timestamp helper (avoid NameError in scheduler catch-up)."""
    return datetime.now(timezone.utc).isoformat()


class NotificationServiceError(Exception):
    """Raised when notification operations fail."""


class NotificationNotFoundError(NotificationServiceError):
    """Raised when a notification cannot be found."""


def _get_notifications_collection() -> AsyncIOMotorCollection:
    return get_database()[NOTIFICATIONS_COLLECTION]


def _get_runs_collection() -> AsyncIOMotorCollection:
    return get_database()[AUTOMATION_RUNS_COLLECTION]


async def ensure_notification_indexes() -> None:
    collection = _get_notifications_collection()
    await collection.create_index([("created_at", -1)])
    await collection.create_index("read")
    await collection.create_index("type")
    await collection.create_index("priority")
    await collection.create_index("preference_id")

    runs = _get_runs_collection()
    await runs.create_index([("started_at", -1)])
    await runs.create_index("run_type")
    await runs.create_index("preference_id")
    logger.info("Notification and automation_runs indexes ensured")


async def create_notification(payload: NotificationCreate) -> NotificationDocument:
    collection = _get_notifications_collection()
    now = _utc_now_iso()
    document: dict[str, Any] = {
        "type": payload.type,
        "title": payload.title.strip(),
        "message": payload.message.strip(),
        "channel": payload.channel,
        "priority": payload.priority,
        "read": False,
        "metadata": payload.metadata or {},
        "preference_id": payload.preference_id.strip(),
        "created_at": now,
    }
    result = await collection.insert_one(document)
    document["_id"] = result.inserted_id
    notification = NotificationDocument.from_mongo(document)

    try:
        from app.realtime.notification_event_service import emit_notification_created

        await emit_notification_created(notification)
    except Exception:
        logger.exception("Failed to emit realtime notification event")

    return notification


async def list_notifications(
    *,
    unread_only: bool = False,
    notification_type: str | None = None,
    limit: int = 50,
) -> NotificationListResponse:
    collection = _get_notifications_collection()
    query: dict[str, Any] = {}
    if unread_only:
        query["read"] = False
    if notification_type:
        query["type"] = notification_type.strip()

    total = await collection.count_documents(query)
    unread_count = await collection.count_documents({**query, "read": False})
    cursor = collection.find(query).sort("created_at", -1).limit(min(limit, 200))
    documents = await cursor.to_list(length=limit)
    return NotificationListResponse(
        notifications=[NotificationDocument.from_mongo(doc) for doc in documents],
        unread_count=unread_count,
        total=total,
    )


async def get_unread_count() -> int:
    collection = _get_notifications_collection()
    return await collection.count_documents({"read": False})


async def mark_notification_read(notification_id: str) -> NotificationDocument:
    collection = _get_notifications_collection()
    try:
        oid = ObjectId(notification_id)
    except InvalidId as exc:
        raise NotificationNotFoundError("Notification not found") from exc

    result = await collection.find_one_and_update(
        {"_id": oid},
        {"$set": {"read": True}},
        return_document=True,
    )
    if not result:
        raise NotificationNotFoundError("Notification not found")
    return NotificationDocument.from_mongo(result)


async def mark_all_notifications_read() -> int:
    collection = _get_notifications_collection()
    result = await collection.update_many({"read": False}, {"$set": {"read": True}})
    return result.modified_count


async def start_automation_run(
    run_type: str,
    preference_id: str = "",
) -> str:
    collection = _get_runs_collection()
    now = _utc_now_iso()
    document = {
        "run_type": run_type,
        "status": "running",
        "preference_id": preference_id,
        "scan_id": "",
        "jobs_analyzed": 0,
        "high_matches_found": 0,
        "notifications_sent": 0,
        "providers_succeeded": [],
        "providers_failed": [],
        "error": "",
        "started_at": now,
        "completed_at": "",
        "metadata": {},
    }
    result = await collection.insert_one(document)
    return str(result.inserted_id)


async def complete_automation_run(
    run_id: str,
    *,
    status: str = "completed",
    scan_id: str = "",
    jobs_analyzed: int = 0,
    high_matches_found: int = 0,
    notifications_sent: int = 0,
    providers_succeeded: list[str] | None = None,
    providers_failed: list[str] | None = None,
    error: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    collection = _get_runs_collection()
    try:
        oid = ObjectId(run_id)
    except InvalidId:
        return

    await collection.update_one(
        {"_id": oid},
        {
            "$set": {
                "status": status,
                "scan_id": scan_id,
                "jobs_analyzed": jobs_analyzed,
                "high_matches_found": high_matches_found,
                "notifications_sent": notifications_sent,
                "providers_succeeded": providers_succeeded or [],
                "providers_failed": providers_failed or [],
                "error": error,
                "completed_at": _utc_now_iso(),
                "metadata": metadata or {},
            }
        },
    )


async def get_automation_analytics(limit: int = 10) -> dict[str, Any]:
    runs_col = _get_runs_collection()
    cursor = runs_col.find({}).sort("started_at", -1).limit(limit)
    recent_docs = await cursor.to_list(length=limit)
    recent_runs = [AutomationRunDocument.from_mongo(doc) for doc in recent_docs]

    all_runs = await runs_col.find({"status": "completed"}).to_list(length=500)
    scans_completed = sum(1 for r in all_runs if r.get("run_type") == "daily_scan")
    jobs_analyzed = sum(r.get("jobs_analyzed", 0) for r in all_runs)
    notifications_sent = sum(r.get("notifications_sent", 0) for r in all_runs)
    high_matches_found = sum(r.get("high_matches_found", 0) for r in all_runs)

    provider_counter: Counter[str] = Counter()
    for run in all_runs:
        for source in run.get("providers_succeeded") or []:
            provider_counter[source] += 1

    return {
        "scans_completed": scans_completed,
        "jobs_analyzed": jobs_analyzed,
        "notifications_sent": notifications_sent,
        "high_matches_found": high_matches_found,
        "provider_performance": dict(provider_counter.most_common(10)),
        "recent_runs": recent_runs,
    }


async def send_daily_digest_email(
    preferences: UserPreferencesDocument,
    jobs: list[JobDocument],
    *,
    remote_jobs: list[JobDocument],
    easy_apply_jobs: list[JobDocument],
    skills_to_learn: list[str],
    application_summary: dict[str, int],
    provider_stats: dict[str, int],
    insights: list[str],
    scan_summary: ScanEmailSummary | None = None,
) -> bool:
    """Send scheduled scan email with job cards (same format as manual scan emails)."""
    if not preferences.email_notifications:
        return False

    _ = remote_jobs, easy_apply_jobs, skills_to_learn, application_summary, provider_stats, insights

    summary = scan_summary or ScanEmailSummary()
    try:
        if jobs:
            built = build_opportunities_email(jobs[:15], summary, preferences.email)
        else:
            built = build_no_match_email(summary)
        _dispatch_resend(preferences.email, built)
        return True
    except (EmailNotConfiguredError, EmailServiceError) as exc:
        logger.warning("[DIGEST_EMAIL_FAILED] %s", exc)
        return False


async def notify_high_match_jobs(
    preferences: UserPreferencesDocument,
    high_match_jobs: list[JobDocument],
) -> int:
    """Create in-app + optional email alerts for high-priority matches."""
    if not preferences.high_match_alerts or not high_match_jobs:
        return 0

    sent = 0
    for job in high_match_jobs[:5]:
        title = f"New {job.match_percentage}% match found"
        message = f"{job.title} at {job.company} — high priority match on {_format_source_label(job.source)}"

        if preferences.in_app_notifications:
            await create_notification(
                NotificationCreate(
                    type="high_match",
                    title=title,
                    message=message,
                    channel="in_app",
                    priority="high",
                    preference_id=preferences.id,
                    metadata={
                        "job_id": job.id,
                        "match_score": job.match_percentage,
                        "company": job.company,
                        "source": job.source,
                        "apply_url": job.apply_url,
                    },
                )
            )
            sent += 1

        if preferences.email_notifications and job.match_percentage >= HIGH_MATCH_THRESHOLD:
            try:
                summary = ScanEmailSummary()
                built = build_opportunities_email([job], summary, preferences.email)
                built.subject = f"Career OS — {job.match_percentage}% Match: {job.title}"
                _dispatch_resend(preferences.email, built)
            except (EmailNotConfiguredError, EmailServiceError):
                pass

    return sent


async def notify_scan_complete(
    preferences: UserPreferencesDocument,
    *,
    jobs_count: int,
    high_matches: int,
    scan_id: str,
) -> None:
    if not preferences.in_app_notifications:
        return

    await create_notification(
        NotificationCreate(
            type="scan_complete",
            title="Daily job scan complete",
            message=f"Analyzed opportunities — {jobs_count} jobs stored, {high_matches} high matches found.",
            channel="in_app",
            priority="normal",
            preference_id=preferences.id,
            metadata={"scan_id": scan_id, "jobs_count": jobs_count, "high_matches": high_matches},
        )
    )


async def notify_remote_jobs_batch(
    preferences: UserPreferencesDocument,
    remote_jobs: list[JobDocument],
) -> None:
    if not preferences.in_app_notifications or not remote_jobs:
        return

    count = len(remote_jobs)
    if count < 3:
        return

    await create_notification(
        NotificationCreate(
            type="remote_jobs",
            title=f"{count} new remote jobs available",
            message=f"Today's scan found {count} remote opportunities matching your profile.",
            channel="in_app",
            priority="normal",
            preference_id=preferences.id,
            metadata={"count": count},
        )
    )


async def notify_follow_up_reminder(
    preferences: UserPreferencesDocument,
    *,
    title: str,
    company: str,
    application_id: str,
    days_since_applied: int,
) -> None:
    if not preferences.follow_up_reminders or not preferences.in_app_notifications:
        return

    await create_notification(
        NotificationCreate(
            type="follow_up",
            title="Application follow-up reminder",
            message=f"Applied to {title} at {company} {days_since_applied} days ago — consider following up.",
            channel="in_app",
            priority="normal",
            preference_id=preferences.id,
            metadata={
                "application_id": application_id,
                "company": company,
                "suggestion": "Follow up with recruiter",
            },
        )
    )


async def notify_interview_reminder(
    preferences: UserPreferencesDocument,
    *,
    title: str,
    company: str,
    application_id: str,
) -> None:
    if not preferences.in_app_notifications:
        return

    await create_notification(
        NotificationCreate(
            type="interview_reminder",
            title="Interview preparation reminder",
            message=f"Prepare for your interview process at {company} for {title}.",
            channel="in_app",
            priority="high",
            preference_id=preferences.id,
            metadata={
                "application_id": application_id,
                "suggestion": "Prepare for interview",
            },
        )
    )


async def notify_weekly_insights(
    preferences: UserPreferencesDocument,
    insight_messages: list[str],
) -> None:
    if not preferences.in_app_notifications or not insight_messages:
        return

    preview = insight_messages[0][:120]
    await create_notification(
        NotificationCreate(
            type="weekly_insights",
            title="Weekly career insights ready",
            message=preview,
            channel="in_app",
            priority="normal",
            preference_id=preferences.id,
            metadata={"insights": insight_messages},
        )
    )
