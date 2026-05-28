"""Career analytics dashboard facade — aggregates all analytics services."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from app.db.mongo_perf import run_timed
from app.services.job_service import prime_analytics_job_caches
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

logger = logging.getLogger(__name__)


def _empty_salary() -> dict[str, Any]:
    return {
        "average_salary": "—",
        "salary_range": "",
        "top_paying_skills": [],
        "salary_growth_trend": "Run a job scan to unlock salary insights",
        "remote_salary_premium": "",
        "provider_salary_distribution": [],
        "primary_role": "",
        "salary_data_points": 0,
    }


def _empty_market_trends() -> dict[str, Any]:
    return {
        "most_demanded_technologies": [],
        "fastest_growing_roles": [],
        "rising_technologies": [],
        "declining_technologies": [],
        "remote_market_pct": 0,
        "remote_trend": "low",
        "trend_insights": ["Run a job scan to see market trends."],
        "hiring_spikes": [],
        "primary_role": "",
        "total_jobs_analyzed": 0,
    }


def _empty_skill_demand() -> dict[str, Any]:
    return {
        "demand_scores": [],
        "strongest_skills": [],
        "missing_high_value_skills": [],
        "learning_priorities": [],
        "growth_opportunities": [],
        "user_skill_count": 0,
        "market_skill_count": 0,
        "top_missing_from_matches": [],
    }


def _empty_conversion() -> dict[str, Any]:
    return {
        "funnel": [],
        "overall_response_rate": 0,
        "provider_conversion": [],
    }


def _empty_providers() -> dict[str, Any]:
    return {
        "providers": [],
        "best_match_provider": "",
        "best_interview_conversion": None,
        "most_remote_opportunities": None,
        "summary": [],
    }


def _empty_growth() -> dict[str, Any]:
    return {
        "career_growth_score": 0,
        "primary_role": "",
        "insights": ["Complete a scan to generate career growth insights."],
        "avg_market_match": 0,
        "high_match_roles": 0,
        "skill_coverage_score": 0,
        "market_fit_score": 0,
    }


def _empty_transitions() -> dict[str, Any]:
    return {"current_role": "", "suggested_transitions": []}


def _empty_heatmap() -> dict[str, Any]:
    return {
        "heatmap": [],
        "remote_opportunity_density": 0,
        "strongest_hiring_cities": [],
    }


def _empty_weekly() -> dict[str, Any]:
    return {
        "strongest_opportunities": [],
        "top_missing_skill": "—",
        "career_growth_score": 0,
        "headline": "Run a job scan to unlock weekly insights",
        "summary_lines": [],
    }


async def _safe_section(
    name: str,
    coro: Awaitable[dict[str, Any]],
    default: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    try:
        result = await coro
        if not isinstance(result, dict):
            raise TypeError(f"section {name} returned {type(result)!r}")
        return result
    except Exception:
        logger.exception("[CAREER_ANALYTICS] section_failed name=%s", name)
        return default()


async def build_analytics_dashboard(target_role: str | None = None) -> dict[str, Any]:
    """Full career intelligence dashboard payload, optionally scoped to a target role."""

    async def _assemble() -> dict[str, Any]:
        # One Mongo round-trip per cache before parallel sections (avoids 8× find_latest_scan_jobs).
        await prime_analytics_job_caches()

        (
            salary,
            market_trends,
            skill_demand,
            conversion,
            providers,
            growth,
            transitions,
            heatmap,
            weekly,
        ) = await asyncio.gather(
            _safe_section(
                "salary",
                build_salary_insights(target_role=target_role),
                _empty_salary,
            ),
            _safe_section("market_trends", build_market_trends(), _empty_market_trends),
            _safe_section(
                "skill_demand",
                build_skill_demand_analytics(target_role=target_role),
                _empty_skill_demand,
            ),
            _safe_section(
                "application_funnel",
                build_application_conversion_analytics(),
                _empty_conversion,
            ),
            _safe_section(
                "provider_performance",
                build_provider_performance(),
                _empty_providers,
            ),
            _safe_section("career_growth", build_career_growth_insights(), _empty_growth),
            _safe_section("role_transitions", build_role_transitions(), _empty_transitions),
            _safe_section("market_heatmap", build_job_market_heatmap(), _empty_heatmap),
            _safe_section("weekly_insights", build_weekly_insights(), _empty_weekly),
        )

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

    return await run_timed("career_analytics_dashboard", _assemble)
