import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import CurrentUser, get_current_user
from app.core.config import settings
from app.services.cache_service import get_json, set_json
from app.utils.cache_keys import scans_latest_user_key, scans_recent_user_key
from app.models.scan_session import ScanSessionDocument, ScanSummaryDetail
from app.services.scan_session_service import (
    ScanSessionServiceError,
    get_latest_scan_session,
    get_scan_session_by_scan_id,
    list_recent_scan_sessions,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scan-analytics"])


@router.get("/scan-analytics/latest", response_model=ScanSummaryDetail | None)
async def latest_scan_analytics(
    current_user: CurrentUser = Depends(get_current_user),
) -> ScanSummaryDetail | None:
    """Return analytics for the most recent scan session."""
    cache_key = scans_latest_user_key(current_user.user_id)
    cached = get_json(cache_key)
    if cached is not None:
        return ScanSummaryDetail(**cached)

    try:
        session = await get_latest_scan_session(current_user.user_id)
        if not session:
            return None
        payload = session.to_summary_detail().model_dump(mode="json")
        set_json(cache_key, payload, settings.CACHE_RESPONSE_TTL)
        return ScanSummaryDetail(**payload)
    except ScanSessionServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching scan analytics")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc


@router.get("/scan-analytics/recent")
async def recent_scan_analytics(
    limit: int = 10,
    current_user: CurrentUser = Depends(get_current_user),
) -> list[ScanSummaryDetail]:
    limit = min(max(1, limit), 50)
    cache_key = scans_recent_user_key(current_user.user_id, limit=limit)
    cached = get_json(cache_key)
    if cached is not None:
        return [ScanSummaryDetail(**item) for item in cached]

    try:
        sessions = await list_recent_scan_sessions(current_user.user_id, limit=limit)
        payload = [session.to_summary_detail().model_dump(mode="json") for session in sessions]
        set_json(cache_key, payload, settings.CACHE_RESPONSE_TTL)
        return [ScanSummaryDetail(**item) for item in payload]
    except ScanSessionServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error listing scan analytics")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc


@router.get("/scan-analytics/session/{scan_id}", response_model=ScanSessionDocument | None)
async def scan_session_detail(
    scan_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ScanSessionDocument | None:
    try:
        session = await get_scan_session_by_scan_id(scan_id, user_id=current_user.user_id)
        return session
    except ScanSessionServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching scan session")
        raise HTTPException(status_code=500, detail={"message": "An unexpected error occurred"}) from exc
