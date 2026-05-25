from typing import Any

from app.realtime.websocket_manager import publish_user_event


async def emit_automation_started(
    user_id: str,
    *,
    run_id: str,
    run_type: str,
    preference_id: str = "",
) -> None:
    await publish_user_event(
        user_id,
        "automation_started",
        run_id=run_id,
        run_type=run_type,
        preference_id=preference_id,
        message=f"Automation started ({run_type})",
    )


async def emit_automation_finished(
    user_id: str,
    *,
    run_id: str,
    status: str,
    jobs_analyzed: int = 0,
    high_matches: int = 0,
    **extra: Any,
) -> None:
    await publish_user_event(
        user_id,
        "automation_finished",
        run_id=run_id,
        status=status,
        jobs_analyzed=jobs_analyzed,
        high_matches=high_matches,
        message=f"Automation {status}",
        **extra,
    )


async def emit_email_delivered(
    user_id: str,
    *,
    scan_id: str,
    to_email: str,
) -> None:
    await publish_user_event(
        user_id,
        "email_delivered",
        scan_id=scan_id,
        to_email=to_email,
        message=f"Digest email delivered to {to_email}",
    )
