"""Interview advisor — readiness gaps and prep priorities."""

from __future__ import annotations

from typing import Any


def advise_interview(context: dict[str, Any]) -> dict[str, Any]:
    market = context.get("market", {})
    apps = context.get("applications", {})
    jobs_ctx = context.get("jobs", {})
    resume = context.get("resume", {})

    missing_skills = market.get("top_missing_skills") or []
    growth = market.get("growth_score", 0)
    primary_role = market.get("primary_role", "Software Engineering")

    weak_areas: list[str] = []
    for skill in missing_skills[:5]:
        weak_areas.append(f"Technical gap: {skill}")

    app_analytics = apps.get("analytics", {})
    if app_analytics.get("interviews", 0) == 0 and app_analytics.get("total_applied", 0) >= 3:
        weak_areas.append("Application-to-interview conversion — focus on higher match roles")

    prep_priorities: list[str] = []
    if missing_skills:
        prep_priorities.append(f"Study {missing_skills[0]} — common in your target roles")
    prep_priorities.append(f"Prepare for {primary_role} behavioral questions")
    if jobs_ctx.get("top_jobs"):
        top = jobs_ctx["top_jobs"][0]
        prep_priorities.append(f"Review requirements for {top['title']} at {top['company']}")

    confidence_tips: list[str] = []
    if growth >= 60:
        confidence_tips.append("Your career growth score suggests solid market alignment — focus on depth.")
    else:
        confidence_tips.append("Build confidence by practicing mock interviews for your top 3 matched roles.")
    if resume.get("skills"):
        confidence_tips.append(f"Leverage existing skills in answers: {', '.join(resume['skills'][:4])}")

    return {
        "weak_areas": weak_areas[:6],
        "preparation_priorities": prep_priorities[:5],
        "confidence_recommendations": confidence_tips,
        "primary_role": primary_role,
        "summary": (
            f"Focus interview prep on {primary_role} roles. "
            + (f"Top skill gap: {missing_skills[0]}." if missing_skills else "Run a scan to identify skill gaps.")
        ),
    }
