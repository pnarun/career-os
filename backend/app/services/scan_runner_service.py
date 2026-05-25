import logging
from dataclasses import dataclass, field

from app.realtime.automation_stream_service import emit_email_delivered
from app.realtime.scan_event_service import (
    emit_scan_completed,
    emit_scan_failed,
    emit_scan_started,
)
from app.models.job import JobDocument, ScanFetchResponse
from app.services.scan_session_service import get_latest_scan_session, get_scan_session_by_scan_id
from app.models.user_preferences import UserPreferencesDocument
from app.services.email_service import (
    EmailNotConfiguredError,
    EmailServiceError,
    ScanEmailSummary,
    send_scan_results_email,
)
from app.services.job_service import (
    JobDiscoveryError,
    JobServiceError,
    discover_and_store_jobs,
    get_latest_scan_jobs,
)
from app.services.resume_service import ResumeNotFoundError, get_resume_by_id
from app.core.user_context import set_request_user
from app.services.user_preferences_service import mark_email_sent

logger = logging.getLogger(__name__)


class ScanRunnerError(Exception):
    """Raised when a scan cannot complete."""


@dataclass
class EmailDeliveryResult:
    sent: bool = False
    to_email: str = ""
    error: str = ""
    skipped_reason: str = ""


@dataclass
class ScanRunResult:
    preference_id: str
    scan_id: str
    scan_timestamp: str
    stored: int
    emailed: bool
    email_skipped_reason: str = ""
    top_jobs: list[JobDocument] = field(default_factory=list)
    email_result: EmailDeliveryResult = field(default_factory=EmailDeliveryResult)
    scan_summary: ScanFetchResponse | None = None
    manual: bool = False


async def _resolve_email_analytics(
    scan_id: str,
    fetch_response: ScanFetchResponse | None,
    *,
    user_id: str = "",
):
    if fetch_response and fetch_response.scan_summary:
        return fetch_response.scan_summary
    session = await get_scan_session_by_scan_id(scan_id, user_id=user_id or None)
    if session:
        return session.to_summary_detail()
    latest = await get_latest_scan_session(user_id) if user_id else None
    if latest and latest.scan_id == scan_id:
        return latest.to_summary_detail()
    return None


async def _deliver_scan_email(
    preferences: UserPreferencesDocument,
    jobs: list[JobDocument],
    scan_id: str,
    scan_timestamp: str,
    *,
    manual: bool,
    last_email_scan_id: str,
    fetch_response: ScanFetchResponse | None = None,
) -> EmailDeliveryResult:
    result = EmailDeliveryResult(to_email=preferences.email)

    if not manual and last_email_scan_id == scan_id:
        result.skipped_reason = "duplicate_scan_email"
        logger.info(
            "[EMAIL_SKIPPED] preference_id=%s scan_id=%s reason=already_sent",
            preferences.id,
            scan_id,
        )
        return result

    try:
        analytics = await _resolve_email_analytics(
            scan_id,
            fetch_response,
            user_id=preferences.user_id,
        )

        delivery = send_scan_results_email(
            email=preferences.email,
            jobs=jobs,
            scan_summary=ScanEmailSummary(
                scan_id=scan_id,
                scan_timestamp=scan_timestamp,
                analytics=analytics,
            ),
        )
        result.sent = delivery.sent
        if delivery.sent and not manual:
            await mark_email_sent(preferences.id, scan_id)
    except EmailNotConfiguredError:
        result.skipped_reason = "email_not_configured"
        result.error = "Resend is not configured"
        logger.warning(
            "[EMAIL_SKIPPED] preference_id=%s reason=resend_not_configured",
            preferences.id,
        )
    except EmailServiceError as exc:
        result.skipped_reason = "email_send_failed"
        result.error = str(exc)
        logger.error(
            "[EMAIL_SENT_FAILURE] preference_id=%s error=%s",
            preferences.id,
            exc,
        )

    return result


async def _execute_scan(
    preferences: UserPreferencesDocument,
    *,
    manual: bool = False,
) -> ScanRunResult:
    log_tag = "[MANUAL_SCAN_TRIGGERED]" if manual else "[SCHEDULED_SCAN_STARTED]"
    logger.info(
        "%s preference_id=%s email=%s resume_id=%s",
        log_tag,
        preferences.id,
        preferences.email,
        preferences.resume_id,
    )

    if not manual and not preferences.is_active:
        logger.info(
            "[SCHEDULED_SCAN_SKIPPED] preference_id=%s reason=inactive",
            preferences.id,
        )
        return ScanRunResult(
            preference_id=preferences.id,
            scan_id="",
            scan_timestamp="",
            stored=0,
            emailed=False,
            email_skipped_reason="inactive",
            manual=manual,
        )

    user_id = preferences.user_id or ""
    if user_id:
        set_request_user(user_id, preferences.workspace_id or "")

    if user_id:
        await emit_scan_started(
            user_id,
            manual=manual,
            preference_id=preferences.id,
        )

    try:
        await get_resume_by_id(preferences.resume_id)
    except ResumeNotFoundError as exc:
        logger.error(
            "[SCAN_FAILED] preference_id=%s reason=resume_not_found manual=%s",
            preferences.id,
            manual,
        )
        if user_id:
            await emit_scan_failed(user_id, reason="resume_not_found", manual=manual)
        raise ScanRunnerError(str(exc)) from exc

    try:
        scan_summary = await discover_and_store_jobs(resume_id=preferences.resume_id)
    except JobDiscoveryError as exc:
        logger.error(
            "[SCAN_FAILED] preference_id=%s reason=%s manual=%s",
            preferences.id,
            exc,
            manual,
        )
        if user_id:
            await emit_scan_failed(user_id, reason=str(exc), manual=manual)
        raise ScanRunnerError(str(exc)) from exc
    except JobServiceError as exc:
        logger.error(
            "[SCAN_FAILED] preference_id=%s reason=job_service manual=%s",
            preferences.id,
            manual,
        )
        if user_id:
            await emit_scan_failed(user_id, reason="job_service_error", manual=manual)
        raise ScanRunnerError(str(exc)) from exc

    latest_jobs = await get_latest_scan_jobs()
    email_delivery = await _deliver_scan_email(
        preferences,
        latest_jobs,
        scan_summary.scan_id,
        scan_summary.scan_timestamp,
        manual=manual,
        last_email_scan_id=preferences.last_email_scan_id,
        fetch_response=scan_summary,
    )

    emailed = email_delivery.sent
    skip_reason = email_delivery.skipped_reason

    if user_id:
        await emit_scan_completed(
            user_id,
            scan_id=scan_summary.scan_id,
            stored=scan_summary.stored,
            emailed=emailed,
            manual=manual,
        )
        if emailed:
            await emit_email_delivered(
                user_id,
                scan_id=scan_summary.scan_id,
                to_email=preferences.email,
            )

    logger.info(
        "[SCAN_COMPLETED] preference_id=%s scan_id=%s stored=%d emailed=%s manual=%s",
        preferences.id,
        scan_summary.scan_id,
        scan_summary.stored,
        emailed,
        manual,
    )

    return ScanRunResult(
        preference_id=preferences.id,
        scan_id=scan_summary.scan_id,
        scan_timestamp=scan_summary.scan_timestamp,
        stored=scan_summary.stored,
        emailed=emailed,
        email_skipped_reason=skip_reason,
        top_jobs=latest_jobs[:15],
        email_result=email_delivery,
        scan_summary=scan_summary,
        manual=manual,
    )


async def run_scan_for_user(
    preferences: UserPreferencesDocument,
) -> ScanRunResult:
    """Scheduled scan orchestration (respects active flag and duplicate email guard)."""
    return await _execute_scan(preferences, manual=False)


async def run_scan_now(
    preferences: UserPreferencesDocument,
) -> ScanRunResult:
    """
    Manual on-demand scan: always runs immediately and sends one email per click.
    Bypasses inactive check and duplicate-email guard for controlled testing.
    """
    return await _execute_scan(preferences, manual=True)
