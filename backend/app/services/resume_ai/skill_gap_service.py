"""Skill gap analysis from resume vs market demand."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.models.resume import ResumeDocument
from app.services.resume_ai._resume_utils import resume_skill_set
from app.utils.skills_master import TECH_STACK_GROUPS, categorize_skills, extract_skills_from_text


def analyze_skill_gaps(
    resume: ResumeDocument,
    *,
    market_jobs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate skill gaps, strengths, and learning recommendations."""
    resume_skills = list(resume_skill_set(resume.raw_text, resume.skills))
    categories = categorize_skills([s for s in resume.skills] or extract_skills_from_text(resume.raw_text))

    market_demand: Counter[str] = Counter()
    missing_from_jobs: Counter[str] = Counter()

    for job in market_jobs or []:
        for skill in extract_skills_from_text(job.get("description", "")):
            market_demand[skill] += 1
        for skill in job.get("missing_skills") or []:
            missing_from_jobs[skill.strip()] += 1

    top_missing: list[dict[str, Any]] = []
    resume_set = set(resume_skills)
    demand_source = missing_from_jobs if missing_from_jobs else market_demand

    for skill, count in demand_source.most_common(12):
        if skill.lower() not in resume_set:
            top_missing.append({
                "skill": skill,
                "demand_count": count,
                "priority": "high" if count >= 3 else "medium",
            })

    strongest_area = _strongest_area(categories)
    growth_recommendation = _growth_recommendation(categories, top_missing)

    learning_recs: list[dict[str, str]] = []
    for gap in top_missing[:5]:
        learning_recs.append({
            "skill": gap["skill"],
            "recommendation": f"Consider upskilling in {gap['skill']} — appears in {gap['demand_count']} relevant roles",
            "type": "market_demand",
        })

    radar_data = _skill_radar(categories)

    return {
        "top_missing_skills": top_missing[:8],
        "strongest_area": strongest_area,
        "growth_recommendation": growth_recommendation,
        "learning_recommendations": learning_recs,
        "skill_radar": radar_data,
        "resume_skill_count": len(resume_skills),
    }


def _strongest_area(categories: dict[str, list[str]]) -> str:
    if not any(categories.values()):
        return "General software engineering"
    best = max(categories.items(), key=lambda x: len(x[1]))
    labels = {
        "frontend": "Frontend Development",
        "backend": "Backend APIs",
        "data": "Data & Databases",
        "cloud_devops": "Cloud Infrastructure",
        "ml": "AI / Machine Learning",
    }
    return labels.get(best[0], best[0].title())


def _growth_recommendation(
    categories: dict[str, list[str]],
    top_missing: list[dict[str, Any]],
) -> str:
    if top_missing:
        return f"Cloud & platform skills — top gap: {top_missing[0]['skill']}"
    weak_groups = [name for name, skills in categories.items() if not skills]
    if "cloud_devops" in weak_groups:
        return "Cloud Infrastructure"
    if "ml" in weak_groups:
        return "AI / Machine Learning"
    return "Full-stack breadth"


def _skill_radar(categories: dict[str, list[str]]) -> list[dict[str, Any]]:
    max_skills = max((len(v) for v in categories.values()), default=1) or 1
    labels = {
        "frontend": "Frontend",
        "backend": "Backend",
        "data": "Data",
        "cloud_devops": "DevOps",
        "ml": "AI/ML",
    }
    radar: list[dict[str, Any]] = []
    for group in TECH_STACK_GROUPS:
        count = len(categories.get(group, []))
        radar.append({
            "category": labels.get(group, group),
            "score": int(count / max_skills * 100) if max_skills else 0,
            "skills": categories.get(group, []),
        })
    return radar
