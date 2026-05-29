import logging

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.user_context import require_request_user_id
from app.services.cache_service import get_json, set_json
from app.services.dashboard_service import get_dashboard_summary
from app.utils.cache_keys import dashboard_user_key
from app.services.application_service import ApplicationServiceError
from app.services.job_service import JobServiceError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
async def read_dashboard_summary() -> dict:
    """Lightweight home dashboard stats (no full jobs feed)."""
    user_id = require_request_user_id()
    cache_key = dashboard_user_key(user_id)
    cached = get_json(cache_key)
    if cached is not None:
        return cached

    try:
        payload = await get_dashboard_summary()
        set_json(cache_key, payload, settings.CACHE_RESPONSE_TTL)
        return payload
    except (ApplicationServiceError, JobServiceError) as exc:
        logger.error("Dashboard summary failed: %s", exc)
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception(
            "Unexpected dashboard summary error user_id=%s",
            user_id,
            extra={"event": "dashboard_summary_failed", "user_id": user_id},
        )
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to load dashboard summary"},
        ) from exc
