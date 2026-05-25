"""Market reasoning — explain trends relative to user profile."""

from __future__ import annotations

from typing import Any


def reason_about_market(context: dict[str, Any]) -> dict[str, Any]:
    market = context.get("market", {})
    jobs_ctx = context.get("jobs", {})
    resume = context.get("resume", {})

    trends = market.get("market_trends", {})
    skill_demand = market.get("skill_demand", {})
    transitions = market.get("role_transitions", {})
    primary_role = market.get("primary_role", "")

    insights: list[str] = []
    reasons: list[str] = []

    for item in (trends.get("trend_insights") or [])[:3]:
        insights.append(item)
        reasons.append("Derived from your latest job scan trends")

    demand_scores = skill_demand.get("demand_scores") or []
    top_tech = demand_scores[0] if demand_scores else None
    if top_tech:
        insights.append(
            f"{top_tech.get('skill', '')} appears in {top_tech.get('demand_pct', 0)}% of roles in your scan."
        )
        reasons.append("Skill demand computed from matched job descriptions")

    resume_skills = {s.lower() for s in resume.get("skills", [])}
    combo_hits: list[str] = []
    if "python" in resume_skills or any("python" in s for s in resume_skills):
        for tech in ("fastapi", "aws", "docker", "kubernetes"):
            for ds in demand_scores[:10]:
                if tech in ds.get("skill", "").lower() and ds.get("demand_pct", 0) >= 25:
                    combo_hits.append(f"{ds['skill']} + Python")
                    break
    for combo in combo_hits[:2]:
        insights.append(f"{combo} combination is trending in your matching roles.")
        reasons.append("Cross-referenced resume skills with market demand")

    if primary_role:
        insights.append(f"Your profile aligns strongest with {primary_role} roles.")
        reasons.append("Inferred from job title patterns in your scan")

    missing = skill_demand.get("missing_high_value_skills") or []
    if missing:
        m = missing[0]
        insights.append(
            f"Adding {m.get('skill', '')} could unlock more high-paying opportunities ({m.get('demand_pct', 0)}% demand)."
        )
        reasons.append("Missing high-value skill from skill demand analytics")

    current_role = transitions.get("current_role", primary_role)
    if transitions.get("suggested_transitions"):
        t = transitions["suggested_transitions"][0]
        insights.append(f"Career path option: {current_role} → {t.get('target_role', '')}.")
        reasons.append(t.get("reason", "Based on skill overlap and market demand"))

    return {
        "market_insights": insights[:8],
        "reasons": reasons[:6],
        "primary_role": primary_role or current_role,
        "remote_pct": trends.get("remote_market_pct", 0),
        "summary": insights[0] if insights else "Run a job scan to generate market reasoning.",
    }
