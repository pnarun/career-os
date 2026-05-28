import logging

from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.core.user_context import require_request_user_id
from app.models.career_analytics import CareerAnalyticsDashboard
from app.services.cache_service import get_json, set_json
from app.services.career_analytics.analytics_dashboard_service import build_analytics_dashboard
from app.utils.cache_keys import analytics_user_key
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

router = APIRouter(tags=["career-analytics"])


@router.get("/career-analytics/dashboard", response_model=CareerAnalyticsDashboard)
async def career_analytics_dashboard(
    role: str = Query(default="", description="Target role for role-specific analytics"),
) -> CareerAnalyticsDashboard:
    """Full career intelligence dashboard."""
    role_key = role.strip() or None
    user_id = require_request_user_id()
    cache_key = analytics_user_key(user_id, role=role.strip())
    cached = get_json(cache_key)
    if cached is not None:
        return CareerAnalyticsDashboard(**cached)

    logger.info("[CAREER_ANALYTICS] dashboard start role=%s", role_key or "(default)")
    try:
        data = await build_analytics_dashboard(target_role=role_key)
        logger.info("[CAREER_ANALYTICS] dashboard ok role=%s", role_key or "(default)")
        set_json(cache_key, data, settings.CACHE_RESPONSE_TTL)
        return CareerAnalyticsDashboard(**data)
    except Exception as exc:
        logger.exception("Failed to build career analytics dashboard")
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Career analytics is temporarily unavailable. Try again in a moment.",
                "error": str(exc),
            },
        ) from exc


@router.get("/career-analytics/salary")
async def salary_insights() -> dict:
    try:
        return await build_salary_insights()
    except Exception as exc:
        logger.exception("Failed to build salary insights")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/career-analytics/market-trends")
async def market_trends() -> dict:
    try:
        return await build_market_trends()
    except Exception as exc:
        logger.exception("Failed to build market trends")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/career-analytics/skill-demand")
async def skill_demand() -> dict:
    try:
        return await build_skill_demand_analytics()
    except Exception as exc:
        logger.exception("Failed to build skill demand analytics")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/career-analytics/application-funnel")
async def application_funnel() -> dict:
    try:
        return await build_application_conversion_analytics()
    except Exception as exc:
        logger.exception("Failed to build application funnel")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/career-analytics/providers")
async def provider_performance() -> dict:
    try:
        return await build_provider_performance()
    except Exception as exc:
        logger.exception("Failed to build provider performance")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/career-analytics/growth")
async def career_growth() -> dict:
    try:
        return await build_career_growth_insights()
    except Exception as exc:
        logger.exception("Failed to build career growth insights")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/career-analytics/transitions")
async def role_transitions() -> dict:
    try:
        return await build_role_transitions()
    except Exception as exc:
        logger.exception("Failed to build role transitions")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/career-analytics/heatmap")
async def market_heatmap() -> dict:
    try:
        return await build_job_market_heatmap()
    except Exception as exc:
        logger.exception("Failed to build market heatmap")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/career-analytics/weekly-insights")
async def weekly_insights() -> dict:
    try:
        return await build_weekly_insights()
    except Exception as exc:
        logger.exception("Failed to build weekly insights")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc
