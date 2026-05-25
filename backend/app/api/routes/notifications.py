import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.automation_run import AutomationAnalytics
from app.models.career_insight import CareerInsightDocument, CareerInsightsSummary
from app.models.notification import NotificationDocument, NotificationListResponse
from app.services.career_insight_service import generate_career_insights, list_career_insights
from app.services.notification_service import (
    NotificationNotFoundError,
    NotificationServiceError,
    get_automation_analytics,
    get_unread_count,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.services.user_preferences_service import get_preferences

logger = logging.getLogger(__name__)

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=NotificationListResponse)
async def read_notifications(
    unread_only: bool = Query(False),
    type: str | None = Query(None, alias="type"),
    limit: int = Query(50, ge=1, le=200),
) -> NotificationListResponse:
    try:
        return await list_notifications(
            unread_only=unread_only,
            notification_type=type,
            limit=limit,
        )
    except NotificationServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc


@router.get("/notifications/unread-count")
async def read_unread_count() -> dict[str, int]:
    try:
        count = await get_unread_count()
        return {"unread_count": count}
    except NotificationServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc


@router.patch("/notifications/{notification_id}/read", response_model=NotificationDocument)
async def patch_notification_read(notification_id: str) -> NotificationDocument:
    try:
        return await mark_notification_read(notification_id)
    except NotificationNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except NotificationServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc


@router.post("/notifications/read-all")
async def post_mark_all_read() -> dict[str, int]:
    try:
        count = await mark_all_notifications_read()
        return {"marked_read": count}
    except NotificationServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc


@router.get("/automation/analytics", response_model=AutomationAnalytics)
async def read_automation_analytics(
    limit: int = Query(10, ge=1, le=50),
) -> AutomationAnalytics:
    try:
        data = await get_automation_analytics(limit=limit)
        return AutomationAnalytics(**data)
    except NotificationServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc


@router.get("/career-insights", response_model=list[CareerInsightDocument])
async def read_career_insights(
    limit: int = Query(20, ge=1, le=100),
) -> list[CareerInsightDocument]:
    try:
        return await list_career_insights(limit=limit)
    except Exception as exc:
        logger.exception("Failed to list career insights")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.post("/career-insights/generate", response_model=CareerInsightsSummary)
async def post_generate_career_insights() -> CareerInsightsSummary:
    try:
        preferences = await get_preferences()
        return await generate_career_insights(preferences)
    except Exception as exc:
        logger.exception("Failed to generate career insights")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc
