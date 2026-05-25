import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.application import (
    ApplicationAnalytics,
    ApplicationCreatePayload,
    ApplicationDocument,
    ApplicationNotesUpdate,
    ApplicationStatusUpdate,
    ApplicationTimelineResponse,
    TimelineEvent,
)
from app.services.application_service import (
    ApplicationNotFoundError,
    ApplicationServiceError,
    build_application_analytics,
    build_job_application_map,
    delete_application,
    get_application_by_job_id,
    get_application_timeline,
    list_applications,
    mark_applied,
    save_job,
    update_application_notes,
    update_application_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["applications"])


@router.post("/applications/save", response_model=ApplicationDocument)
async def save_application(payload: ApplicationCreatePayload) -> ApplicationDocument:
    try:
        return await save_job(payload)
    except ApplicationServiceError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Failed to save application")
        raise HTTPException(status_code=500, detail={"message": "Failed to save job"}) from exc


@router.post("/applications/apply", response_model=ApplicationDocument)
async def apply_application(payload: ApplicationCreatePayload) -> ApplicationDocument:
    """Track manual apply action — does not auto-submit to employers."""
    try:
        return await mark_applied(payload)
    except ApplicationServiceError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Failed to mark application applied")
        raise HTTPException(status_code=500, detail={"message": "Failed to track apply"}) from exc


@router.patch("/applications/{application_id}/status", response_model=ApplicationDocument)
async def patch_application_status(
    application_id: str,
    body: ApplicationStatusUpdate,
) -> ApplicationDocument:
    try:
        return await update_application_status(application_id, body.status)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except ApplicationServiceError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Failed to update application status")
        raise HTTPException(status_code=500, detail={"message": "Status update failed"}) from exc


@router.patch("/applications/{application_id}/notes", response_model=ApplicationDocument)
async def patch_application_notes(
    application_id: str,
    body: ApplicationNotesUpdate,
) -> ApplicationDocument:
    try:
        return await update_application_notes(application_id, body.notes)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Failed to update application notes")
        raise HTTPException(status_code=500, detail={"message": "Notes update failed"}) from exc


@router.get("/applications/job-map")
async def get_applications_job_map() -> dict[str, ApplicationDocument]:
    """Bulk lookup map keyed by job_id (avoids per-card API calls on Jobs page)."""
    try:
        mapping = await build_job_application_map()
        return {
            job_id: app.model_dump()
            for job_id, app in mapping.items()
        }
    except ApplicationServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc


@router.get("/applications", response_model=list[ApplicationDocument])
async def get_applications(
    status: str | None = None,
    source: str | None = None,
    remote: bool | None = None,
    min_match: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    job_id: str | None = None,
    page: int | None = Query(None, ge=1),
    limit: int | None = Query(None, ge=1, le=500),
) -> list[ApplicationDocument]:
    try:
        if job_id:
            application = await get_application_by_job_id(job_id)
            return [application] if application else []
        return await list_applications(
            status=status,
            source=source,
            remote=remote,
            min_match=min_match,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
        )
    except ApplicationServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Failed to list applications")
        raise HTTPException(status_code=500, detail={"message": "Failed to list applications"}) from exc


@router.get("/applications/analytics", response_model=ApplicationAnalytics)
async def get_applications_analytics() -> ApplicationAnalytics:
    try:
        return await build_application_analytics()
    except ApplicationServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Failed to build application analytics")
        raise HTTPException(status_code=500, detail={"message": "Analytics failed"}) from exc


@router.get("/applications/timeline", response_model=ApplicationTimelineResponse)
async def get_applications_timeline(
    application_id: str | None = Query(None),
) -> ApplicationTimelineResponse:
    try:
        events = await get_application_timeline(application_id)
        return ApplicationTimelineResponse(events=events)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except ApplicationServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Failed to fetch application timeline")
        raise HTTPException(status_code=500, detail={"message": "Timeline failed"}) from exc


@router.delete("/applications/{application_id}")
async def remove_application(application_id: str) -> dict[str, str]:
    try:
        await delete_application(application_id)
        return {"message": "Application deleted"}
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Failed to delete application")
        raise HTTPException(status_code=500, detail={"message": "Delete failed"}) from exc
