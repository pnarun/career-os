import logging

from fastapi import APIRouter, HTTPException

from app.models.job import JobDocument, JobHistoryItem, ScanFetchResponse
from app.models.linkedin_fetch import LinkedInFetchResponse
from app.models.unified_feed import UnifiedFeedResponse
from app.services.job_service import (
    JobDiscoveryError,
    JobServiceError,
    discover_and_store_jobs,
    fetch_and_merge_linkedin_jobs,
    get_job_history,
    get_latest_scan_jobs,
    get_unified_jobs_feed,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])


@router.post("/fetch-linkedin", response_model=LinkedInFetchResponse)
async def fetch_linkedin_jobs() -> LinkedInFetchResponse:
    """Background LinkedIn discovery using saved session; merges into latest scan feed."""
    try:
        return await fetch_and_merge_linkedin_jobs()
    except JobDiscoveryError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except JobServiceError as exc:
        logger.error("LinkedIn job fetch failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"message": "Job service unavailable"},
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during LinkedIn fetch")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred during LinkedIn fetch"},
        ) from exc


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


@router.get("/jobs/history")
async def list_job_history(
    page: int = 1,
    limit: int = 50,
) -> dict:
    """Return paginated job history (all scans, newest first)."""
    try:
        items, total = await get_job_history(page=page, limit=limit)
        return {
            "items": items,
            "total": total,
            "page": max(1, page),
            "limit": min(max(1, limit), 500),
        }
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


@router.get("/jobs/feed", response_model=UnifiedFeedResponse)
async def get_jobs_feed(
    providers: str | None = None,
    remote_only: bool = False,
    easy_apply_only: bool = False,
    min_match: int | None = None,
    keyword: str | None = None,
    sort: str = "default",
    strong_matches_only: bool = False,
    remote_high_match: bool = False,
    easy_apply_high_match: bool = False,
    company: str | None = None,
) -> UnifiedFeedResponse:
    """Return the unified multi-provider jobs feed from the latest scan."""
    provider_list = [p.strip() for p in providers.split(",")] if providers else None
    try:
        return await get_unified_jobs_feed(
            providers=provider_list,
            remote_only=remote_only,
            easy_apply_only=easy_apply_only,
            min_match=min_match,
            keyword=keyword,
            sort_by=sort,
            strong_matches_only=strong_matches_only,
            remote_high_match=remote_high_match,
            easy_apply_high_match=easy_apply_high_match,
            company=company,
        )
    except JobServiceError as exc:
        logger.error("Failed to build unified jobs feed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"message": "Unable to build unified jobs feed"},
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error building unified jobs feed")
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
