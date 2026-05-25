"""Career growth insights and growth score."""

from __future__ import annotations

from typing import Any

from app.services.application_service import build_application_analytics
from app.services.career_analytics._analytics_utils import (
    ROLE_TRANSITIONS,
    collect_market_skills,
    infer_primary_role,
)
from app.services.career_analytics.skill_demand_service import build_skill_demand_analytics
from app.services.job_service import get_latest_scan_jobs
from app.services.resume_service import get_all_resumes
from app.services.user_preferences_service import get_preferences


async def build_career_growth_insights() -> dict[str, Any]:
    jobs = await get_latest_scan_jobs()
    preferences = await get_preferences()
    skill_demand = await build_skill_demand_analytics()
    app_analytics = await build_application_analytics()

    primary_role = infer_primary_role(jobs)
    resume_skills: list[str] = []
    if preferences and preferences.resume_id:
        try:
            from app.services.resume_service import get_resume_by_id
            resume = await get_resume_by_id(preferences.resume_id)
            resume_skills = list(resume.skills or [])
        except Exception:
            pass
    if not resume_skills:
        resumes = await get_all_resumes()
        if resumes:
            resume_skills = list(resumes[0].skills or [])

    market_skills = collect_market_skills(jobs)
    avg_match = int(sum(j.match_percentage for j in jobs) / len(jobs)) if jobs else 0
    high_matches = sum(1 for j in jobs if j.match_percentage >= 75)

    insights: list[str] = [
        f"Your profile is strongest for {primary_role} roles.",
    ]

    missing = skill_demand.get("missing_high_value_skills") or []
    if missing:
        top = missing[0]
        insights.append(
            f"{top['skill']} appears in {top['demand_pct']}% of roles — high-value skill to learn."
        )

    skill_pairs: list[str] = []
    resume_lower = {s.lower() for s in resume_skills}
    if "python" in resume_lower or any("python" in s.lower() for s in resume_skills):
        if market_skills.get("Docker", 0) >= 3 or market_skills.get("Kubernetes", 0) >= 2:
            skill_pairs.append("DevOps + Python combination has high market demand.")
    if any("react" in s.lower() for s in resume_skills) and market_skills.get("TypeScript", 0) >= 3:
        skill_pairs.append("React + TypeScript stack aligns with strong frontend hiring.")
    if market_skills.get("AWS", 0) >= 5:
        insights.append("Cloud infrastructure skills could increase salary potential.")
    insights.extend(skill_pairs)

    if app_analytics.response_rate >= 15:
        insights.append(f"Application response rate ({app_analytics.response_rate}%) shows positive momentum.")
    elif app_analytics.total_applied >= 3:
        insights.append("Consider targeting higher match-score roles to improve response rates.")

    growth_score = _compute_growth_score(
        avg_match=avg_match,
        high_matches=high_matches,
        skill_coverage=len(skill_demand.get("strongest_skills") or []),
        missing_count=len(missing),
        response_rate=app_analytics.response_rate,
        total_jobs=len(jobs),
    )

    return {
        "career_growth_score": growth_score,
        "primary_role": primary_role,
        "insights": insights[:8],
        "avg_market_match": avg_match,
        "high_match_roles": high_matches,
        "skill_coverage_score": min(100, len(skill_demand.get("strongest_skills") or []) * 12),
        "market_fit_score": min(100, avg_match),
    }


def _compute_growth_score(
    *,
    avg_match: int,
    high_matches: int,
    skill_coverage: int,
    missing_count: int,
    response_rate: float,
    total_jobs: int,
) -> int:
    score = 0.0
    score += min(30, avg_match * 0.3)
    score += min(20, high_matches * 2)
    score += min(20, skill_coverage * 2.5)
    score += min(15, response_rate * 0.75)
    score += min(15, total_jobs / 10)
    score -= min(10, missing_count)
    return max(0, min(100, int(round(score))))


async def build_weekly_insights() -> dict[str, Any]:
    """Automated weekly-style summary for dashboard."""
    growth = await build_career_growth_insights()
    skill_demand = await build_skill_demand_analytics()
    jobs = await get_latest_scan_jobs()

    opportunities: list[str] = []
    for job in sorted(jobs, key=lambda j: j.match_percentage, reverse=True)[:5]:
        if job.match_percentage >= 60:
            remote_tag = "Remote " if job.remote_priority else ""
            opportunities.append(f"{remote_tag}{job.title} at {job.company}")

    top_missing = (skill_demand.get("learning_priorities") or [{}])[0]
    top_missing_skill = top_missing.get("skill", "N/A") if top_missing else "N/A"

    return {
        "strongest_opportunities": opportunities[:5],
        "top_missing_skill": top_missing_skill,
        "career_growth_score": growth["career_growth_score"],
        "headline": growth["insights"][0] if growth.get("insights") else "",
        "summary_lines": growth.get("insights", [])[:4],
    }
