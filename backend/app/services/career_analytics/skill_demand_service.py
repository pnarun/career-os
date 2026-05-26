"""Skill demand analytics — user skills vs market demand."""

from __future__ import annotations

from typing import Any

from app.services.career_analytics._analytics_utils import (
    SKILL_SALARY_PREMIUM,
    collect_market_skills,
)
from app.services.career_insight_service import get_top_missing_skills
from app.services.job_service import get_latest_scan_jobs
from app.services.resume_service import get_all_resumes
from app.services.user_preferences_service import get_preferences


async def build_skill_demand_analytics(target_role: str | None = None) -> dict[str, Any]:
    jobs = await get_latest_scan_jobs()
    if target_role and target_role.strip():
        needle = target_role.strip().lower()
        jobs = [
            j for j in jobs
            if needle in (j.title or "").lower()
            or needle in (j.description or "").lower()
        ]
    preferences = await get_preferences()
    market_skills = collect_market_skills(jobs)
    total_jobs = len(jobs) or 1

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

    resume_set = {s.lower() for s in resume_skills}
    demand_scores: list[dict[str, Any]] = []
    for skill, count in market_skills.most_common(20):
        demand_pct = int(round(count / total_jobs * 100))
        has_skill = skill.lower() in resume_set or any(
            skill.lower() in rs.lower() or rs.lower() in skill.lower() for rs in resume_skills
        )
        roi = SKILL_SALARY_PREMIUM.get(skill, 3000 if demand_pct >= 40 else 1000)
        demand_scores.append({
            "skill": skill,
            "demand_score": min(100, demand_pct + min(count, 20)),
            "demand_pct": demand_pct,
            "job_count": count,
            "user_has_skill": has_skill,
            "salary_roi_estimate": roi,
        })

    missing_high_value = [
        item for item in demand_scores
        if not item["user_has_skill"] and item["demand_pct"] >= 25
    ]
    missing_high_value.sort(key=lambda x: (x["demand_score"], x["salary_roi_estimate"]), reverse=True)

    strongest = [
        item for item in demand_scores if item["user_has_skill"]
    ][:8]

    learning_priorities = [
        {
            "skill": item["skill"],
            "demand_pct": item["demand_pct"],
            "priority": "high" if item["demand_pct"] >= 50 else "medium" if item["demand_pct"] >= 30 else "low",
            "salary_roi_estimate": item["salary_roi_estimate"],
            "reason": f"Appears in {item['demand_pct']}% of matching roles",
        }
        for item in missing_high_value[:8]
    ]

    growth_opportunities = [
        f"Adding {item['skill']} could unlock {item['demand_pct']}% more role matches."
        for item in missing_high_value[:4]
    ]

    insight_missing = get_top_missing_skills(jobs)

    return {
        "demand_scores": demand_scores,
        "strongest_skills": strongest,
        "missing_high_value_skills": missing_high_value[:10],
        "learning_priorities": learning_priorities,
        "growth_opportunities": growth_opportunities,
        "user_skill_count": len(resume_skills),
        "market_skill_count": len(market_skills),
        "top_missing_from_matches": insight_missing,
    }
