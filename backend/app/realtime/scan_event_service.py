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
) -> None:
    await publish_user_event(
        user_id,
        "scan_started",
        scan_id=scan_id,
        manual=manual,
        preference_id=preference_id,
        message="Job scan started",
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
) -> None:
    await publish_user_event(
        user_id,
        "scan_completed",
        scan_id=scan_id,
        stored=stored,
        emailed=emailed,
        manual=manual,
        message=f"Scan complete — {stored} jobs stored",
    )


async def emit_scan_failed(
    user_id: str,
    *,
    reason: str,
    manual: bool = False,
) -> None:
    await publish_user_event(
        user_id,
        "scan_failed",
        reason=reason,
        manual=manual,
        message=f"Scan failed: {reason}",
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
