"""Aggregate user + platform intelligence into one copilot context."""

from __future__ import annotations

from typing import Any

from app.services.application_service import build_application_analytics, list_applications
from app.services.career_analytics.analytics_dashboard_service import build_analytics_dashboard
from app.services.career_insight_service import get_top_missing_skills
from app.services.job_service import get_latest_scan_jobs
from app.services.notification_service import get_automation_analytics
from app.services.resume_service import get_all_resumes, get_resume_by_id
from app.services.user_preferences_service import get_preferences


async def build_user_context() -> dict[str, Any]:
    """Build the full grounded context layer for copilot reasoning."""
    preferences = await get_preferences()
    jobs = await get_latest_scan_jobs()
    applications = await list_applications()
    app_analytics = await build_application_analytics()
    resumes = await get_all_resumes()

    resume_skills: list[str] = []
    resume_id = ""
    if preferences and preferences.resume_id:
        resume_id = preferences.resume_id
        try:
            resume = await get_resume_by_id(resume_id)
            resume_skills = list(resume.skills or [])
        except Exception:
            pass
    elif resumes:
        resume_id = resumes[0].id
        resume_skills = list(resumes[0].skills or [])

    high_matches = [j for j in jobs if j.match_percentage >= 75]
    medium_matches = [j for j in jobs if 55 <= j.match_percentage < 75]
    low_matches = [j for j in jobs if j.match_percentage < 55]
    remote_jobs = [j for j in jobs if j.remote_priority]

    avg_match = int(sum(j.match_percentage for j in jobs) / len(jobs)) if jobs else 0

    try:
        analytics = await build_analytics_dashboard()
    except Exception:
        analytics = {}

    try:
        automation = await get_automation_analytics(limit=5)
    except Exception:
        automation = {}

    return {
        "resume": {
            "resume_id": resume_id,
            "skills": resume_skills[:20],
            "skill_count": len(resume_skills),
        },
        "jobs": {
            "total": len(jobs),
            "avg_match": avg_match,
            "high_match_count": len(high_matches),
            "medium_match_count": len(medium_matches),
            "low_match_count": len(low_matches),
            "remote_count": len(remote_jobs),
            "top_jobs": [
                {
                    "title": j.title,
                    "company": j.company,
                    "source": j.source,
                    "match_percentage": j.match_percentage,
                    "remote": j.remote_priority,
                    "missing_skills": (j.missing_skills or [])[:5],
                    "matched_skills": (j.matched_skills or [])[:5],
                }
                for j in sorted(jobs, key=lambda x: x.match_percentage, reverse=True)[:8]
            ],
        },
        "applications": {
            "total": len(applications),
            "analytics": app_analytics.model_dump() if hasattr(app_analytics, "model_dump") else {},
            "recent": [
                {
                    "title": a.title,
                    "company": a.company,
                    "status": a.status,
                    "source": a.source,
                    "match_score": a.match_score,
                }
                for a in applications[:8]
            ],
        },
        "market": {
            "growth_score": analytics.get("career_growth_score", 0),
            "primary_role": analytics.get("career_growth", {}).get("primary_role", ""),
            "top_missing_skills": get_top_missing_skills(jobs),
            "weekly_insights": analytics.get("weekly_insights", {}),
            "skill_demand": analytics.get("skill_demand", {}),
            "provider_performance": analytics.get("provider_performance", {}),
            "market_trends": analytics.get("market_trends", {}),
            "role_transitions": analytics.get("role_transitions", {}),
            "application_funnel": analytics.get("application_funnel", {}),
        },
        "automation": automation,
        "preferences": {
            "remote_only": bool(preferences and preferences.remote_only),
            "min_match_threshold": preferences.min_match_threshold if preferences else 0,
            "expected_salary": preferences.expected_salary if preferences else "",
        },
    }
