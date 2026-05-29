import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import CurrentUser, get_current_user
from app.core.config import settings
from app.models.scan import (
    EmailPreviewResponse,
    RunScanNowRequest,
    RunScanNowResponse,
    ScanTaskStatusResponse,
    SendEmailNowRequest,
    SendEmailNowResponse,
)
from app.services.email_service import (
    EmailNotConfiguredError,
    EmailServiceError,
    ScanEmailSummary,
    generate_email_preview,
    send_scan_results_email,
)
from app.models.job import JobDocument
from app.services.job_service import JobServiceError, get_latest_scan_jobs
from app.scan_execution import scan_execution_manager
from app.services.scan_runner_service import ScanRunnerError
from app.services.scan_session_service import (
    ScanSessionServiceError,
    get_latest_scan_session,
)
from app.services.user_preferences_service import (
    UserPreferencesNotFoundError,
    UserPreferencesServiceError,
    get_preferences_by_id,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scan"])


def _latest_scan_meta(jobs: list[JobDocument]) -> tuple[str, str]:
    """Safe scan_id and timestamp from latest batch (empty when no jobs)."""
    if not jobs:
        return "", ""
    first = jobs[0]
    scan_id = first.scan_id or ""
    scan_timestamp = first.scan_timestamp or first.created_at or ""
    return scan_id, scan_timestamp


@router.post("/run-scan-now", response_model=RunScanNowResponse)
async def trigger_manual_scan(
    payload: RunScanNowRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> RunScanNowResponse:
    """Run an immediate scan and send curated opportunity email."""
    try:
        preferences = await get_preferences_by_id(
            payload.preferences_id,
            user_id=current_user.user_id,
        )

        if settings.QUEUE_SCANS_ENABLED and settings.CELERY_ENABLED:
            from app.queues.scan_tasks import run_manual_scan_task

            task = run_manual_scan_task.delay(
                payload.preferences_id,
                current_user.user_id,
            )
            return RunScanNowResponse(
                status="queued",
                email_to=preferences.email,
                task_id=task.id,
            )

        result = await scan_execution_manager.run_manual_scan_now(
            preferences,
            user_id=current_user.user_id,
            workspace_id=current_user.workspace_id or "",
            email=current_user.email or "",
        )

        if result.queued:
            return RunScanNowResponse(
                status="queued",
                email_to=preferences.email,
                task_id=result.task_id,
            )

        scan_result = result.result
        if scan_result is None:
            raise ScanRunnerError("Manual scan returned no result")

        email_error = scan_result.email_result.error or scan_result.email_skipped_reason

        return RunScanNowResponse(
            status="success",
            scan_id=scan_result.scan_id,
            jobs_found=len(scan_result.top_jobs),
            email_sent=scan_result.emailed,
            email_to=preferences.email,
            scan_timestamp=scan_result.scan_timestamp,
            stored=scan_result.stored,
            email_error=email_error if not scan_result.emailed else "",
            task_id=result.task_id,
        )
    except UserPreferencesNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except ScanRunnerError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except EmailServiceError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except UserPreferencesServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception(
            "Unexpected error during manual scan preference_id=%s",
            payload.preferences_id,
            extra={"event": "manual_scan_failed", "preference_id": payload.preferences_id},
        )
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc


@router.get("/scan-tasks/{task_id}", response_model=ScanTaskStatusResponse)
async def get_scan_task_status(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ScanTaskStatusResponse:
    """Lightweight dispatch task status (dispatch mode)."""
    payload = await scan_execution_manager.get_task_status(
        task_id,
        user_id=current_user.user_id,
    )
    if payload is None:
        raise HTTPException(status_code=404, detail={"message": "Scan task not found"})
    return ScanTaskStatusResponse(**payload)


@router.post("/send-email-now", response_model=SendEmailNowResponse)
async def send_email_now(
    payload: SendEmailNowRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> SendEmailNowResponse:
    """Send email for the latest scan batch without running a new scan."""
    try:
        preferences = await get_preferences_by_id(
            payload.preferences_id,
            user_id=current_user.user_id,
        )
        jobs = await get_latest_scan_jobs()
        scan_id, scan_timestamp = _latest_scan_meta(jobs)

        analytics = None
        session = await get_latest_scan_session(current_user.user_id)
        if session:
            analytics = session.to_summary_detail()

        delivery = send_scan_results_email(
            email=preferences.email,
            jobs=jobs,
            scan_summary=ScanEmailSummary(
                scan_id=scan_id,
                scan_timestamp=scan_timestamp,
                analytics=analytics,
            ),
        )

        return SendEmailNowResponse(
            status="success",
            email_sent=delivery.sent,
            jobs_sent=delivery.jobs_sent,
            email_to=delivery.email_to,
            email_type=delivery.email_type,
            sent_at=delivery.sent_at,
        )
    except UserPreferencesNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except EmailNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except EmailServiceError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except JobServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error sending email")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc


@router.get("/email-preview", response_model=EmailPreviewResponse)
async def email_preview(
    resume_id: str | None = Query(None, description="Optional resume id for context"),
    current_user: CurrentUser = Depends(get_current_user),
) -> EmailPreviewResponse:
    """Return HTML email preview from the latest scan batch without sending."""
    del resume_id

    try:
        jobs = await get_latest_scan_jobs()
        scan_id, scan_timestamp = _latest_scan_meta(jobs)

        analytics = None
        session = await get_latest_scan_session(current_user.user_id)
        if session:
            analytics = session.to_summary_detail()

        preview_html = generate_email_preview(
            jobs,
            scan_timestamp=scan_timestamp,
            scan_id=scan_id,
            analytics=analytics,
        )

        return EmailPreviewResponse(
            preview_html=preview_html,
            jobs_count=min(len(jobs), 15),
            scan_id=scan_id,
            scan_timestamp=scan_timestamp,
        )
    except JobServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error generating email preview")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc
