"""Background scan orchestration (FastAPI BackgroundTasks — no Celery)."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from app.core.config import settings
from app.core.user_context import clear_request_user, set_request_user
from app.core.runtime_diagnostics import log_memory_event
from app.services.cache_invalidation import invalidate_after_scan_complete
from app.services.cache_service import set_json
from app.services.job_service import (
    JobDiscoveryError,
    JobServiceError,
    discover_and_store_jobs,
    generate_scan_id,
    get_latest_scan_jobs,
)
from app.realtime.scan_event_service import emit_scan_completed, emit_scan_failed, emit_scan_started
from app.services.scan_runner_service import ScanRunnerError, _deliver_scan_email
from app.services.scan_state_service import (
    complete_scan,
    fail_scan,
    get_scan_state,
    mark_provider_running,
    update_scan_progress,
    update_scan_progress_provider,
)
from app.observability.operational_metrics import record_scan_duration
from app.services.user_preferences_service import (
    UserPreferencesNotFoundError,
    get_preferences_by_id,
)
from app.utils.cache_keys import scans_latest_user_key

logger = logging.getLogger(__name__)

ProviderCallback = Callable[[str, str, int, str], None]


def _provider_callback(scan_id: str) -> ProviderCallback:
    def on_provider(provider: str, status: str, jobs_found: int, error: str) -> None:
        if status == "running":
            mark_provider_running(scan_id, provider)
            return
        update_scan_progress_provider(
            scan_id,
            provider,
            status=status,
            jobs_found=jobs_found,
            error=error,
        )

    return on_provider


async def execute_background_scan(
    *,
    scan_id: str,
    user_id: str,
    workspace_id: str = "",
    email: str = "",
    resume_id: str | None = None,
    preferences_id: str | None = None,
    send_email: bool = False,
) -> None:
    """Run full discover pipeline; update Redis state throughout."""
    set_request_user(user_id, workspace_id, email)
    scan_started_at = time.perf_counter()
    log_memory_event("MEMORY_BEFORE_SCAN", scan_id=scan_id, user_id=user_id)

    try:
        await emit_scan_started(user_id, scan_id=scan_id, manual=True)
        update_scan_progress(scan_id, status="fetching", progress=5)

        result = await discover_and_store_jobs(
            resume_id=resume_id,
            scan_id=scan_id,
            on_provider_complete=_provider_callback(scan_id),
            on_phase=lambda phase, pct: update_scan_progress(
                scan_id, status="processing" if phase != "fetching" else "fetching", progress=pct
            ),
        )

        update_scan_progress(scan_id, status="processing", progress=90, jobs_found=result.stored)

        email_sent = False
        email_error = ""
        if send_email and preferences_id:
            try:
                preferences = await get_preferences_by_id(preferences_id, user_id=user_id)
                jobs = await get_latest_scan_jobs()
                delivery = await _deliver_scan_email(
                    preferences,
                    jobs,
                    result.scan_id,
                    result.scan_timestamp,
                    manual=True,
                    last_email_scan_id=preferences.last_email_scan_id,
                    fetch_response=result,
                )
                email_sent = delivery.sent
                email_error = delivery.error or delivery.skipped_reason
            except UserPreferencesNotFoundError:
                email_error = "preferences_not_found"
            except Exception as exc:
                logger.exception("Background scan email delivery failed scan_id=%s", scan_id)
                email_error = str(exc)

        summary = result.model_dump(mode="json")
        if send_email:
            summary["email_sent"] = email_sent
            summary["email_error"] = email_error

        complete_scan(
            scan_id,
            jobs_stored=result.stored,
            jobs_found=result.fetched,
            result_summary=summary,
        )

        _cache_latest_scan_summary(user_id, summary)
        invalidate_after_scan_complete(user_id)
        duration_ms = (time.perf_counter() - scan_started_at) * 1000
        record_scan_duration(scan_id, duration_ms, status="completed")
        final_state = get_scan_state(scan_id)
        state_payload = final_state.model_dump(mode="json") if final_state else {}
        await emit_scan_completed(
            user_id,
            scan_id=result.scan_id,
            stored=result.stored,
            emailed=email_sent,
            manual=True,
            **{k: v for k, v in state_payload.items() if k not in ("result_summary",)},
        )

    except (JobDiscoveryError, JobServiceError, ScanRunnerError) as exc:
        duration_ms = (time.perf_counter() - scan_started_at) * 1000
        record_scan_duration(scan_id, duration_ms, status="failed")
        logger.exception(
            "Background scan failed scan_id=%s reason=%s",
            scan_id,
            type(exc).__name__,
            extra={"event": "scan_failed", "scan_id": scan_id, "user_id": user_id},
        )
        await emit_scan_failed(user_id, scan_id=scan_id, reason=str(exc), manual=True)
        fail_scan(scan_id, str(exc))
    except Exception as exc:
        logger.exception(
            "Background scan failed scan_id=%s unexpected",
            scan_id,
            extra={"event": "scan_failed", "scan_id": scan_id, "user_id": user_id},
        )
        duration_ms = (time.perf_counter() - scan_started_at) * 1000
        record_scan_duration(scan_id, duration_ms, status="failed")
        await emit_scan_failed(user_id, scan_id=scan_id, reason=str(exc), manual=True)
        fail_scan(scan_id, str(exc))
    finally:
        log_memory_event(
            "MEMORY_AFTER_SCAN",
            scan_id=scan_id,
            user_id=user_id,
            duration_ms=round((time.perf_counter() - scan_started_at) * 1000, 1),
        )
        clear_request_user()


def _cache_latest_scan_summary(user_id: str, summary: dict[str, Any]) -> None:
    """Warm scan-analytics latest cache after successful background scan."""
    if not user_id or not summary:
        return
    scan_detail = summary.get("scan_summary")
    if scan_detail:
        set_json(scans_latest_user_key(user_id), scan_detail, settings.CACHE_RESPONSE_TTL)


def new_scan_id() -> str:
    return generate_scan_id()
