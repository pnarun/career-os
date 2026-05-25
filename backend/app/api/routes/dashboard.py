import logging

from fastapi import APIRouter, HTTPException

from app.services.dashboard_service import get_dashboard_summary
from app.services.application_service import ApplicationServiceError
from app.services.job_service import JobServiceError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
async def read_dashboard_summary() -> dict:
    """Lightweight home dashboard stats (no full jobs feed)."""
    try:
        return await get_dashboard_summary()
    except (ApplicationServiceError, JobServiceError) as exc:
        logger.error("Dashboard summary failed: %s", exc)
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected dashboard summary error")
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to load dashboard summary"},
        ) from exc
