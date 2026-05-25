"""Lightweight dashboard aggregates — avoids full jobs feed on home load."""

from __future__ import annotations

import logging
from typing import Any

from app.services.application_service import build_application_analytics, list_applications
from app.services.job_service import get_latest_scan_jobs
from app.services.notification_service import get_automation_analytics, get_unread_count
from app.core.user_context import get_request_user_id
from app.services.scan_session_service import get_latest_scan_session

logger = logging.getLogger(__name__)

_FEED_PREVIEW_LIMIT = 5
_RECENT_APPS_LIMIT = 5


def _serialize_automation(automation: dict[str, Any] | None) -> dict[str, Any] | None:
    if not automation:
        return None
    payload = dict(automation)
    runs = payload.get("recent_runs") or []
    payload["recent_runs"] = [
        run.model_dump() if hasattr(run, "model_dump") else run for run in runs
    ]
    return payload


async def get_dashboard_summary() -> dict[str, Any]:
    """Return minimal dashboard payload (stats + previews, no full feed blob)."""
    jobs = await get_latest_scan_jobs()
    user_id = get_request_user_id() or ""
    session = await get_latest_scan_session(user_id) if user_id else None
    scan = session.to_summary_detail() if session else None
    application_analytics = await build_application_analytics()
    unread = await get_unread_count()
    automation = await get_automation_analytics(limit=5)
    applications = await list_applications(limit=_RECENT_APPS_LIMIT)

    total_jobs = len(jobs)
    high_matches = sum(1 for j in jobs if (j.match_percentage or 0) >= 75)
    easy_apply = sum(1 for j in jobs if j.easy_apply)

    top_jobs = sorted(
        jobs,
        key=lambda j: j.match_percentage or 0,
        reverse=True,
    )[:_FEED_PREVIEW_LIMIT]

    recent_applications = sorted(
        applications,
        key=lambda a: str(a.updated_at or a.applied_at or ""),
        reverse=True,
    )[:_RECENT_APPS_LIMIT]

    recent_runs = automation.get("recent_runs") or [] if automation else []
    scan_status = "Idle"
    if recent_runs:
        first_run = recent_runs[0]
        scan_status = (
            first_run.status
            if hasattr(first_run, "status")
            else first_run.get("status", "Active")
        ) or "Active"
    elif scan and getattr(scan, "qualified_jobs", 0):
        scan_status = "Ready"

    scan_id = jobs[0].scan_id if jobs else (scan.scan_id if scan else "")
    scan_timestamp = jobs[0].scan_timestamp if jobs else (scan.scan_timestamp if scan else "")

    return {
        "scan": scan.model_dump() if scan else None,
        "application_analytics": application_analytics.model_dump(),
        "feed": {
            "total_jobs": total_jobs,
            "high_matches": high_matches,
            "easy_apply": easy_apply,
            "scan_id": scan_id,
            "scan_timestamp": scan_timestamp,
            "top_jobs": [
                {
                    "id": str(j.id) if j.id else "",
                    "title": j.title,
                    "company": j.company,
                    "source": j.source,
                    "match_percentage": j.match_percentage,
                }
                for j in top_jobs
            ],
        },
        "unread_count": unread,
        "automation": _serialize_automation(automation),
        "scan_status": scan_status,
        "recent_applications": [
            {
                "id": a.application_id,
                "application_id": a.application_id,
                "title": a.title,
                "company": a.company,
                "status": a.status,
                "updated_at": a.updated_at,
            }
            for a in recent_applications
        ],
    }
