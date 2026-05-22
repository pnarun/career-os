import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.scan import (
    EmailPreviewResponse,
    RunScanNowRequest,
    RunScanNowResponse,
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
from app.services.scan_runner_service import ScanRunnerError, run_scan_now
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
async def trigger_manual_scan(payload: RunScanNowRequest) -> RunScanNowResponse:
    """Run an immediate scan and send curated opportunity email."""
    try:
        preferences = await get_preferences_by_id(payload.preferences_id)
        result = await run_scan_now(preferences)

        email_error = result.email_result.error or result.email_skipped_reason

        return RunScanNowResponse(
            status="success",
            scan_id=result.scan_id,
            jobs_found=len(result.top_jobs),
            email_sent=result.emailed,
            email_to=preferences.email,
            scan_timestamp=result.scan_timestamp,
            stored=result.stored,
            email_error=email_error if not result.emailed else "",
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
        logger.exception("Unexpected error during manual scan")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc


@router.post("/send-email-now", response_model=SendEmailNowResponse)
async def send_email_now(payload: SendEmailNowRequest) -> SendEmailNowResponse:
    """Send email for the latest scan batch without running a new scan."""
    try:
        preferences = await get_preferences_by_id(payload.preferences_id)
        jobs = await get_latest_scan_jobs()
        scan_id, scan_timestamp = _latest_scan_meta(jobs)

        delivery = send_scan_results_email(
            email=preferences.email,
            jobs=jobs,
            scan_summary=ScanEmailSummary(
                scan_id=scan_id,
                scan_timestamp=scan_timestamp,
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
) -> EmailPreviewResponse:
    """Return HTML email preview from the latest scan batch without sending."""
    del resume_id  # latest scan batch is global; resume_id reserved for future scoping

    try:
        jobs = await get_latest_scan_jobs()
        scan_id, scan_timestamp = _latest_scan_meta(jobs)

        preview_html = generate_email_preview(
            jobs,
            scan_timestamp=scan_timestamp,
            scan_id=scan_id,
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
