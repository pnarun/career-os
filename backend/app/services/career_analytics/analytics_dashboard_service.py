"""Career analytics dashboard facade — aggregates all analytics services."""

from __future__ import annotations

from typing import Any

from app.services.career_analytics.application_conversion_service import (
    build_application_conversion_analytics,
)
from app.services.career_analytics.career_growth_service import (
    build_career_growth_insights,
    build_weekly_insights,
)
from app.services.career_analytics.job_market_heatmap_service import build_job_market_heatmap
from app.services.career_analytics.market_trend_service import build_market_trends
from app.services.career_analytics.provider_performance_service import build_provider_performance
from app.services.career_analytics.role_transition_service import build_role_transitions
from app.services.career_analytics.salary_insight_service import build_salary_insights
from app.services.career_analytics.skill_demand_service import build_skill_demand_analytics


def _filter_jobs_by_role(jobs: list, target_role: str | None) -> list:
    if not target_role or not target_role.strip():
        return jobs
    needle = target_role.strip().lower()
    return [
        j for j in jobs
        if needle in (getattr(j, "title", "") or "").lower()
        or needle in (getattr(j, "description", "") or "").lower()
    ]


async def build_analytics_dashboard(target_role: str | None = None) -> dict[str, Any]:
    """Full career intelligence dashboard payload, optionally scoped to a target role."""
    salary = await build_salary_insights(target_role=target_role)
    market_trends = await build_market_trends()
    skill_demand = await build_skill_demand_analytics(target_role=target_role)
    conversion = await build_application_conversion_analytics()
    providers = await build_provider_performance()
    growth = await build_career_growth_insights()
    transitions = await build_role_transitions()
    heatmap = await build_job_market_heatmap()
    weekly = await build_weekly_insights()

    return {
        "salary_insights": salary,
        "market_trends": market_trends,
        "skill_demand": skill_demand,
        "application_funnel": conversion,
        "provider_performance": providers,
        "career_growth": growth,
        "role_transitions": transitions,
        "market_heatmap": heatmap,
        "weekly_insights": weekly,
        "career_growth_score": growth.get("career_growth_score", 0),
    }
