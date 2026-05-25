"""List saved/applied jobs with lightweight readiness summaries."""

from __future__ import annotations

from typing import Any

from app.models.application import ApplicationDocument
from app.services.application_service import list_applications
from app.services.interview_ai.interview_ai_facade import get_job_by_id, resolve_resume
from app.services.interview_ai.interview_readiness_service import compute_readiness
from app.services.interview_ai.prep_progress_service import get_progress

PREP_STATUSES = frozenset({"saved", "applied", "interview", "assessment"})

FILTER_MAP: dict[str, frozenset[str]] = {
    "all": PREP_STATUSES,
    "saved": frozenset({"saved"}),
    "applied": frozenset({"applied"}),
    "interview": frozenset({"interview", "assessment"}),
}


async def _job_description_for_app(app: ApplicationDocument) -> tuple[str, str, str]:
    title = app.title
    company = app.company
    description = ""

    if app.job_id:
        try:
            job = await get_job_by_id(app.job_id)
            description = job.description or ""
            title = job.title or title
            company = job.company or company
        except ValueError:
            pass

    if len(description.strip()) < 20:
        skills = ", ".join(app.matched_skills[:12]) if app.matched_skills else ""
        description = (
            f"{title} at {company}. "
            f"Location: {app.location or 'unspecified'}. "
            f"{'Skills: ' + skills + '. ' if skills else ''}"
            f"Software engineering role requiring technical and behavioral interview preparation."
        )

    return description, title, company


async def list_interview_prep_jobs(*, status_filter: str = "all") -> dict[str, Any]:
    """Return prep summaries for saved and applied jobs from the applications CRM."""
    allowed = FILTER_MAP.get(status_filter, PREP_STATUSES)
    applications = await list_applications()
    eligible = [app for app in applications if app.status in allowed]

    resume = await resolve_resume()
    jobs: list[dict[str, Any]] = []

    for app in eligible:
        if not app.job_id and not app.title:
            continue

        description, title, company = await _job_description_for_app(app)
        progress = await get_progress(app.job_id or app.application_id)
        practiced = len(progress.get("practiced_questions", []))
        completed = len(progress.get("completed_topics", []))

        readiness = compute_readiness(
            description,
            job_title=title,
            resume=resume,
            practiced_count=practiced,
            completed_topics=completed,
        )

        jobs.append({
            "job_id": app.job_id or app.application_id,
            "application_id": app.application_id,
            "title": title,
            "company": company,
            "status": app.status,
            "match_score": app.match_score,
            "location": app.location,
            "source": app.source,
            "readiness_score": readiness["readiness_score"],
            "technical_readiness": readiness["technical_readiness"],
            "behavioral_readiness": readiness["behavioral_readiness"],
            "practiced_count": practiced,
            "mock_sessions_completed": progress.get("mock_sessions_completed", 0),
            "focus_label": readiness.get("focus_label", ""),
        })

    jobs.sort(key=lambda j: j["readiness_score"], reverse=True)

    return {
        "jobs": jobs,
        "total": len(jobs),
        "filter": status_filter,
    }
