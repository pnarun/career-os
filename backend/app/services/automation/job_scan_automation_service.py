"""Scheduled job scan automation — scans, scoring, notifications, digests, reminders."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.models.job import JobDocument
from app.models.user_preferences import UserPreferencesDocument
from app.services.application_service import build_application_analytics, list_applications
from app.services.career_insight_service import generate_career_insights, get_insight_messages_for_digest
from app.services.email_service import ScanEmailSummary
from app.services.notification_service import (
    complete_automation_run,
    notify_follow_up_reminder,
    notify_high_match_jobs,
    notify_interview_reminder,
    notify_remote_jobs_batch,
    notify_scan_complete,
    notify_weekly_insights,
    send_daily_digest_email,
    start_automation_run,
)
from app.services.scan_runner_service import ScanRunnerError, run_scan_for_user, run_scan_now
from app.services.user_preferences_service import (
    UserPreferencesNotFoundError,
    get_active_preferences,
    get_preferences_by_id,
    mark_email_sent,
)

logger = logging.getLogger(__name__)

HIGH_MATCH_THRESHOLD = 85
FOLLOW_UP_DAYS = 7


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _filter_jobs_for_preferences(
    jobs: list[JobDocument],
    preferences: UserPreferencesDocument,
) -> list[JobDocument]:
    filtered = jobs
    if preferences.remote_only:
        filtered = [j for j in filtered if j.remote_priority]
    if preferences.min_match_threshold > 0:
        filtered = [j for j in filtered if j.match_percentage >= preferences.min_match_threshold]
    if preferences.preferred_locations:
        locations = {loc.lower() for loc in preferences.preferred_locations}
        filtered = [
            j for j in filtered
            if any(loc in (j.location or "").lower() for loc in locations)
            or j.remote_priority
        ]
    return filtered


def _jobs_eligible_for_alerts(
    jobs: list[JobDocument],
    preferences: UserPreferencesDocument,
) -> list[JobDocument]:
    """
    Email/high-match alerts: India or remote roles only — skip foreign onsite listings.
    """
    filtered = _filter_jobs_for_preferences(jobs, preferences)
    return [
        j for j in filtered
        if getattr(j, "actionable_in_india", True)
        or j.remote_priority
        or j.india_focused
    ]


def _extract_provider_stats(scan_summary) -> tuple[list[str], list[str], dict[str, int]]:
    succeeded: list[str] = []
    failed: list[str] = []
    stats: dict[str, int] = {}
    if scan_summary and scan_summary.scan_summary:
        detail = scan_summary.scan_summary
        stats = dict(detail.sources or {})
        failed = list(detail.failed_sources or [])
        succeeded = [k for k, v in stats.items() if v > 0]
    return succeeded, failed, stats


async def run_daily_job_scan_automation(preference_id: str) -> None:
    """
    Full daily automation flow:
    scan → score → filter → save → notify → digest
    """
    run_id = await start_automation_run("daily_scan", preference_id)
    notifications_sent = 0

    try:
        preferences = await get_preferences_by_id(preference_id)
        if not preferences.is_active:
            await complete_automation_run(run_id, status="completed", metadata={"skipped": "inactive"})
            return

        scan_result = await run_scan_for_user(preferences)
        all_jobs = scan_result.top_jobs or []
        qualified = _filter_jobs_for_preferences(all_jobs, preferences)
        alert_jobs = _jobs_eligible_for_alerts(all_jobs, preferences)
        high_matches = [
            j for j in alert_jobs if j.match_percentage >= HIGH_MATCH_THRESHOLD
        ]

        succeeded, failed, provider_stats = _extract_provider_stats(scan_result)

        if preferences.in_app_notifications:
            await notify_scan_complete(
                preferences,
                jobs_count=scan_result.stored,
                high_matches=len(high_matches),
                scan_id=scan_result.scan_id,
            )
            notifications_sent += 1

            remote_jobs = [j for j in qualified if j.remote_priority]
            await notify_remote_jobs_batch(preferences, remote_jobs)
            if len(remote_jobs) >= 3:
                notifications_sent += 1

        alert_count = await notify_high_match_jobs(preferences, high_matches)
        notifications_sent += alert_count

        app_analytics = await build_application_analytics()
        application_summary = {
            "saved": app_analytics.total_saved,
            "applied": app_analytics.total_applied,
            "interviews": app_analytics.interviews,
            "offers": app_analytics.offers,
        }

        insight_messages = await get_insight_messages_for_digest(preferences)
        remote_jobs = [j for j in qualified if j.remote_priority]
        easy_apply = [j for j in qualified if j.easy_apply or j.is_easy_apply_possible]

        from app.services.career_insight_service import get_top_missing_skills
        skills_to_learn = get_top_missing_skills(all_jobs)

        if preferences.email_notifications and preferences.digest_frequency == "daily":
            digest_sent = await send_daily_digest_email(
                preferences,
                qualified[:15] or all_jobs[:15],
                remote_jobs=remote_jobs,
                easy_apply_jobs=easy_apply,
                skills_to_learn=skills_to_learn,
                application_summary=application_summary,
                provider_stats=provider_stats,
                insights=insight_messages,
                scan_summary=ScanEmailSummary(
                    scan_id=scan_result.scan_id,
                    scan_timestamp=scan_result.scan_timestamp,
                    analytics=scan_result.scan_summary.scan_summary if scan_result.scan_summary else None,
                ),
            )
            if digest_sent:
                notifications_sent += 1
                await mark_email_sent(preferences.id, scan_result.scan_id)

        await complete_automation_run(
            run_id,
            status="completed" if not failed else "partial",
            scan_id=scan_result.scan_id,
            jobs_analyzed=scan_result.stored,
            high_matches_found=len(high_matches),
            notifications_sent=notifications_sent,
            providers_succeeded=succeeded,
            providers_failed=failed,
        )

        logger.info(
            "[DAILY_AUTOMATION_COMPLETE] preference_id=%s scan_id=%s high_matches=%d notifications=%d",
            preference_id,
            scan_result.scan_id,
            len(high_matches),
            notifications_sent,
        )

    except (ScanRunnerError, UserPreferencesNotFoundError) as exc:
        logger.error("[DAILY_AUTOMATION_FAILED] preference_id=%s error=%s", preference_id, exc)
        await complete_automation_run(run_id, status="failed", error=str(exc))
    except Exception as exc:
        logger.exception("[DAILY_AUTOMATION_FAILED] preference_id=%s", preference_id)
        await complete_automation_run(run_id, status="failed", error=str(exc))


async def run_follow_up_reminders() -> None:
    """Remind users about stale applications (applied > 7 days, no status change)."""
    run_id = await start_automation_run("follow_up_reminder")
    sent = 0

    try:
        preferences_list = await get_active_preferences()
        if not preferences_list:
            await complete_automation_run(run_id, status="completed")
            return

        preferences = preferences_list[0]
        if not preferences.follow_up_reminders:
            await complete_automation_run(run_id, status="completed", metadata={"skipped": True})
            return

        applications = await list_applications(status="applied")
        cutoff = datetime.now(timezone.utc) - timedelta(days=FOLLOW_UP_DAYS)

        for app in applications:
            applied_at = _parse_iso(app.applied_at)
            updated_at = _parse_iso(app.updated_at)
            if not applied_at or applied_at > cutoff:
                continue
            if updated_at and updated_at > cutoff:
                continue

            days = (datetime.now(timezone.utc) - applied_at).days
            await notify_follow_up_reminder(
                preferences,
                title=app.title,
                company=app.company,
                application_id=app.application_id,
                days_since_applied=days,
            )
            sent += 1

        await complete_automation_run(run_id, status="completed", notifications_sent=sent)
    except Exception as exc:
        logger.exception("[FOLLOW_UP_REMINDERS_FAILED]")
        await complete_automation_run(run_id, status="failed", error=str(exc))


async def run_interview_reminders() -> None:
    """Remind users with interview/assessment status to prepare or follow up."""
    run_id = await start_automation_run("interview_reminder")
    sent = 0

    try:
        preferences_list = await get_active_preferences()
        if not preferences_list:
            await complete_automation_run(run_id, status="completed")
            return

        preferences = preferences_list[0]
        for status in ("interview", "assessment"):
            applications = await list_applications(status=status)
            for app in applications:
                updated_at = _parse_iso(app.updated_at)
                if updated_at:
                    days_since = (datetime.now(timezone.utc) - updated_at).days
                    if days_since < 1:
                        continue

                await notify_interview_reminder(
                    preferences,
                    title=app.title,
                    company=app.company,
                    application_id=app.application_id,
                )
                sent += 1

        await complete_automation_run(run_id, status="completed", notifications_sent=sent)
    except Exception as exc:
        logger.exception("[INTERVIEW_REMINDERS_FAILED]")
        await complete_automation_run(run_id, status="failed", error=str(exc))


async def run_weekly_career_insights() -> None:
    """Generate and notify weekly career insights."""
    run_id = await start_automation_run("weekly_insights")
    sent = 0

    try:
        preferences_list = await get_active_preferences()
        for preferences in preferences_list:
            if preferences.digest_frequency != "weekly":
                continue

            summary = await generate_career_insights(preferences)
            messages = [doc.message for doc in summary.insights]
            await notify_weekly_insights(preferences, messages)
            sent += 1

            if preferences.email_notifications and messages:
                await send_daily_digest_email(
                    preferences,
                    [],
                    remote_jobs=[],
                    easy_apply_jobs=[],
                    skills_to_learn=summary.top_skills_to_learn,
                    application_summary={
                        "saved": 0,
                        "applied": 0,
                        "interviews": 0,
                        "offers": 0,
                    },
                    provider_stats={},
                    insights=messages,
                )

        await complete_automation_run(run_id, status="completed", notifications_sent=sent)
    except Exception as exc:
        logger.exception("[WEEKLY_INSIGHTS_FAILED]")
        await complete_automation_run(run_id, status="failed", error=str(exc))


async def run_manual_automation_scan(preferences: UserPreferencesDocument):
    """Manual scan with full automation pipeline (notifications + digest)."""
    run_id = await start_automation_run("daily_scan", preferences.id)
    try:
        scan_result = await run_scan_now(preferences)
        all_jobs = scan_result.top_jobs or []
        qualified = _filter_jobs_for_preferences(all_jobs, preferences)
        alert_jobs = _jobs_eligible_for_alerts(all_jobs, preferences)
        high_matches = [
            j for j in alert_jobs if j.match_percentage >= HIGH_MATCH_THRESHOLD
        ]

        alert_count = await notify_high_match_jobs(preferences, high_matches)
        await notify_scan_complete(
            preferences,
            jobs_count=scan_result.stored,
            high_matches=len(high_matches),
            scan_id=scan_result.scan_id,
        )

        await complete_automation_run(
            run_id,
            status="completed",
            scan_id=scan_result.scan_id,
            jobs_analyzed=scan_result.stored,
            high_matches_found=len(high_matches),
            notifications_sent=alert_count + 1,
        )
        return scan_result
    except Exception as exc:
        await complete_automation_run(run_id, status="failed", error=str(exc))
        raise
