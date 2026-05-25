"""Skill advisor — ROI and market-demand skill guidance."""

from __future__ import annotations

from typing import Any


def advise_skills(context: dict[str, Any]) -> dict[str, Any]:
    market = context.get("market", {})
    skill_demand = market.get("skill_demand", {})
    resume = context.get("resume", {})

    high_roi = []
    for item in (skill_demand.get("missing_high_value_skills") or [])[:6]:
        high_roi.append({
            "skill": item.get("skill", ""),
            "demand_pct": item.get("demand_pct", 0),
            "roi_estimate": item.get("salary_roi_estimate", 0),
            "reason": f"Missing from resume · appears in {item.get('demand_pct', 0)}% of roles",
        })

    learning = skill_demand.get("learning_priorities") or []
    strongest = skill_demand.get("strongest_skills") or []
    missing_interview = market.get("top_missing_skills") or []

    recommendations: list[str] = []
    if high_roi:
        top = high_roi[0]
        recommendations.append(
            f"Priority skill: {top['skill']} — high market demand and salary ROI potential."
        )
    if missing_interview:
        recommendations.append(
            f"Most common gap in matching jobs: {missing_interview[0]}."
        )
    if strongest:
        names = ", ".join(s.get("skill", "") for s in strongest[:3])
        recommendations.append(f"Your strongest market-aligned skills: {names}.")

    return {
        "high_roi_skills": high_roi,
        "learning_priorities": learning[:6],
        "strongest_skills": strongest[:6],
        "missing_market_skills": missing_interview[:5],
        "recommendations": recommendations,
        "summary": recommendations[0] if recommendations else "Upload a resume and run a scan for skill guidance.",
    }
