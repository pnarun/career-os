"""Role transition suggestions based on skills and market demand."""

from __future__ import annotations

from typing import Any

from app.services.career_analytics._analytics_utils import (
    ROLE_TRANSITIONS,
    collect_market_skills,
    infer_primary_role,
)
from app.services.career_analytics.salary_insight_service import build_salary_insights
from app.services.job_service import get_latest_scan_jobs
from app.services.resume_service import get_all_resumes
from app.services.user_preferences_service import get_preferences


async def build_role_transitions() -> dict[str, Any]:
    jobs = await get_latest_scan_jobs()
    preferences = await get_preferences()
    primary_role = infer_primary_role(jobs)
    market_skills = collect_market_skills(jobs)

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

    base_transitions = ROLE_TRANSITIONS.get(primary_role, ROLE_TRANSITIONS["general"])
    transitions: list[dict[str, Any]] = []

    for item in base_transitions:
        role = item["role"]
        role_lower = role.lower()
        demand_signals = sum(
            count for skill, count in market_skills.items()
            if skill.lower() in role_lower or any(k in role_lower for k in skill.lower().split())
        )
        transitions.append({
            "target_role": role,
            "reason": item["reason"],
            "market_demand_score": min(100, demand_signals * 5 + 20),
            "skill_overlap": _skill_overlap(resume_skills, role),
            "salary_potential": _salary_potential(role),
        })

    transitions.sort(key=lambda x: (x["market_demand_score"], x["skill_overlap"]), reverse=True)

    salary_data = await build_salary_insights()

    return {
        "current_role": primary_role,
        "suggested_transitions": transitions[:6],
        "market_context": salary_data.get("salary_growth_trend", ""),
        "resume_skills_used": resume_skills[:10],
    }


def _skill_overlap(resume_skills: list[str], target_role: str) -> int:
    role_lower = target_role.lower()
    overlap = 0
    for skill in resume_skills:
        sl = skill.lower()
        if sl in role_lower or any(part in sl for part in role_lower.split()):
            overlap += 1
        elif role_lower.startswith("devops") and sl in ("docker", "kubernetes", "aws", "ci/cd", "terraform"):
            overlap += 1
        elif role_lower.startswith("cloud") and sl in ("aws", "azure", "gcp", "terraform", "kubernetes"):
            overlap += 1
        elif role_lower.startswith("platform") and sl in ("python", "docker", "kubernetes", "microservices"):
            overlap += 1
    return min(100, overlap * 15 + 10)


def _salary_potential(role: str) -> str:
    role_lower = role.lower()
    if "architect" in role_lower or "cloud" in role_lower:
        return "high"
    if "devops" in role_lower or "platform" in role_lower or "sre" in role_lower:
        return "high"
    if "full stack" in role_lower or "backend" in role_lower:
        return "medium-high"
    return "medium"
