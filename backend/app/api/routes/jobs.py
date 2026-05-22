import logging

from fastapi import APIRouter, HTTPException

from app.models.job import JobDocument, JobHistoryItem, ScanFetchResponse
from app.services.job_service import (
    JobDiscoveryError,
    JobServiceError,
    discover_and_store_jobs,
    get_job_history,
    get_latest_scan_jobs,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])


@router.post("/fetch-jobs", response_model=ScanFetchResponse)
async def fetch_jobs() -> ScanFetchResponse:
    """Run a new scan session and store the top curated job batch."""
    try:
        return await discover_and_store_jobs()
    except JobDiscoveryError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except JobServiceError as exc:
        logger.error("Job discovery failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"message": "Job discovery service unavailable"},
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during job discovery")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred during job fetch"},
        ) from exc


@router.get("/jobs/history", response_model=list[JobHistoryItem])
async def list_job_history() -> list[JobHistoryItem]:
    """Return up to 500 historical jobs for debug (all scans, newest first)."""
    try:
        return await get_job_history()
    except JobServiceError as exc:
        logger.error("Failed to list job history: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"message": "Unable to fetch job history"},
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error listing job history")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc


@router.get("/jobs", response_model=list[JobDocument])
async def list_jobs() -> list[JobDocument]:
    """Return only the latest scan batch (up to 50 jobs), prioritized."""
    try:
        return await get_latest_scan_jobs()
    except JobServiceError as exc:
        logger.error("Failed to list jobs: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"message": "Unable to fetch jobs"},
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error listing jobs")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc
