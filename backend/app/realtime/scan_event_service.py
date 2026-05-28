import logging
from typing import Any

from app.realtime.websocket_manager import publish_user_event

logger = logging.getLogger(__name__)


async def emit_scan_started(
    user_id: str,
    *,
    scan_id: str = "",
    manual: bool = False,
    preference_id: str = "",
    **state: Any,
) -> None:
    await publish_user_event(
        user_id,
        "scan_started",
        scan_id=scan_id,
        manual=manual,
        preference_id=preference_id,
        message="Job scan started",
        **state,
    )


async def emit_scan_progress_update(user_id: str, *, event: str = "scan_progress", **data: Any) -> None:
    provider = data.get("current_provider") or ""
    progress = data.get("progress", 0)
    message = f"Scan {progress}%"
    if provider:
        message = f"Scanning {provider}… {progress}%"
    await publish_user_event(
        user_id,
        event,
        message=message,
        **data,
    )


async def emit_provider_started(user_id: str, *, scan_id: str, provider: str, **data: Any) -> None:
    await publish_user_event(
        user_id,
        "provider_started",
        scan_id=scan_id,
        provider=provider,
        current_provider=provider,
        message=f"Started {provider}",
        **data,
    )


async def emit_provider_completed(user_id: str, *, scan_id: str, provider: str, **data: Any) -> None:
    jobs = 0
    providers = data.get("providers") or {}
    if provider in providers:
        jobs = providers[provider].get("jobs_found", 0)
    await publish_user_event(
        user_id,
        "provider_completed",
        scan_id=scan_id,
        provider=provider,
        jobs_found=jobs,
        message=f"{provider} finished ({jobs} jobs)",
        **data,
    )


async def emit_scan_progress(
    user_id: str,
    *,
    scan_id: str,
    stage: str,
    message: str,
    **extra: Any,
) -> None:
    await publish_user_event(
        user_id,
        "scan_progress",
        scan_id=scan_id,
        stage=stage,
        message=message,
        **extra,
    )


async def emit_scan_completed(
    user_id: str,
    *,
    scan_id: str,
    stored: int,
    emailed: bool = False,
    manual: bool = False,
    **state: Any,
) -> None:
    await publish_user_event(
        user_id,
        "scan_completed",
        scan_id=scan_id,
        stored=stored,
        jobs_stored=stored,
        emailed=emailed,
        manual=manual,
        status="completed",
        progress=100,
        message=f"Scan complete — {stored} jobs stored",
        **state,
    )


async def emit_scan_failed(
    user_id: str,
    *,
    scan_id: str = "",
    reason: str,
    manual: bool = False,
    **state: Any,
) -> None:
    await publish_user_event(
        user_id,
        "scan_failed",
        scan_id=scan_id,
        reason=reason,
        manual=manual,
        status="failed",
        message=f"Scan failed: {reason}",
        **state,
    )


async def emit_jobs_fetched(
    user_id: str,
    *,
    provider: str,
    count: int,
    scan_id: str = "",
) -> None:
    await publish_user_event(
        user_id,
        "jobs_fetched",
        provider=provider,
        count=count,
        scan_id=scan_id,
        message=f"{provider.title()} fetched {count} jobs",
    )


async def emit_ai_scoring_complete(
    user_id: str,
    *,
    scan_id: str,
    stored: int,
    matched: int,
) -> None:
    await publish_user_event(
        user_id,
        "ai_scoring_complete",
        scan_id=scan_id,
        stored=stored,
        matched=matched,
        message=f"AI scoring complete — {stored} jobs ranked",
    )
