"""Auto-apply orchestration — safety limits, session lifecycle, post-apply tracking."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.automation.browser.executor import run_playwright
from app.core.config import settings
from app.models.application import ApplicationCreatePayload
from app.models.auto_apply import ApplyConfirmRequest, ApplySessionCreate, ApplySessionDocument
from app.services.application_service import mark_applied
from app.services.auto_apply.apply_history_service import (
    create_apply_session,
    get_apply_analytics,
    get_apply_session,
    record_apply_error,
    record_apply_history,
    session_to_worker_payload,
    update_apply_session,
)
from app.services.auto_apply.confirmation_service import (
    clear_apply_flags,
    signal_apply_cancel,
    signal_apply_confirm,
)
from app.services.resume_service import get_resume_by_id
from app.services.user_preferences_service import get_preferences

logger = logging.getLogger(__name__)

_running_sessions: set[str] = set()


class AutoApplyError(Exception):
    """Raised when auto-apply cannot proceed."""


async def _resolve_apply_preferences() -> dict[str, Any]:
    prefs = await get_preferences()
    if not prefs:
        return {
            "notice_period_days": 30,
            "willing_to_relocate": True,
            "work_authorization": "Authorized to work",
            "expected_salary": "",
        }
    return {
        "notice_period_days": getattr(prefs, "notice_period_days", 30),
        "willing_to_relocate": getattr(prefs, "willing_to_relocate", True),
        "work_authorization": getattr(prefs, "work_authorization", "Authorized to work"),
        "expected_salary": getattr(prefs, "expected_salary", ""),
    }


async def _resolve_resume_id(explicit: str) -> str:
    if explicit.strip():
        return explicit.strip()
    prefs = await get_preferences()
    if prefs and prefs.resume_id:
        return prefs.resume_id
    raise AutoApplyError("No resume configured. Select a resume in Settings.")


async def start_assisted_apply(payload: ApplySessionCreate) -> ApplySessionDocument:
    """Start assisted apply — runs worker in background until confirmation or failure."""
    if not settings.ASSISTED_APPLY_ENABLED:
        raise AutoApplyError(
            "Assisted Apply is disabled. Use Mark Applied or apply on LinkedIn directly."
        )
    logger.info(
        "[AUTO_APPLY] start requested job=%s company=%s source=%s url=%s",
        payload.title,
        payload.company,
        payload.source,
        payload.job_url[:80] if payload.job_url else "",
    )
    analytics = await get_apply_analytics()
    if not analytics.can_apply:
        raise AutoApplyError(
            f"Daily apply limit reached ({analytics.attempts_today}/{analytics.max_per_day}) "
            f"or cooldown active."
        )

    if payload.source.lower() != "linkedin":
        raise AutoApplyError("Only LinkedIn Easy Apply is supported in this phase.")

    resume_id = await _resolve_resume_id(payload.resume_id)
    await get_resume_by_id(resume_id)

    session = await create_apply_session(
        payload.model_copy(update={"resume_id": resume_id})
    )

    if session.session_id in _running_sessions:
        raise AutoApplyError("An apply session is already running.")

    apply_preferences = await _resolve_apply_preferences()
    worker_payload = session_to_worker_payload(session, {
        "apply_preferences": apply_preferences,
    })

    await record_apply_history(session.session_id, "started", {"job_url": session.job_url})
    asyncio.create_task(_run_apply_worker(session.session_id, worker_payload))
    return session


async def _run_apply_worker(session_id: str, worker_payload: dict[str, Any]) -> None:
    _running_sessions.add(session_id)
    try:
        result = await run_playwright(
            "linkedin-easy-apply",
            timeout_sec=660,
            **worker_payload,
        )
        session = await get_apply_session(session_id)
        if not session:
            return

        if result.get("submitted") and session.state == "SUCCESS":
            await _post_apply_success(session)
        elif result.get("status") == "captcha_blocked":
            await record_apply_error(session_id, "CAPTCHA blocked", result)
        elif result.get("status") == "error":
            await record_apply_error(session_id, result.get("message", "Apply failed"), result)
    except Exception as exc:
        logger.exception("[AUTO_APPLY] worker failed session_id=%s", session_id)
        await update_apply_session(session_id, {"state": "FAILED", "error": str(exc)})
        await record_apply_error(session_id, str(exc))
    finally:
        _running_sessions.discard(session_id)
        clear_apply_flags(session_id)


async def _post_apply_success(session: ApplySessionDocument) -> None:
    """Mark application as applied after confirmed submit."""
    try:
        payload = ApplicationCreatePayload(
            job_id=session.job_id,
            title=session.title,
            company=session.company,
            source=session.source,
            apply_url=session.job_url,
            match_score=session.match_score,
            resume_id=session.resume_id,
        )
        application = await mark_applied(payload)
        await update_apply_session(
            session.session_id,
            {"application_id": application.application_id},
        )
        await record_apply_history(session.session_id, "submitted", {
            "application_id": application.application_id,
        })
    except Exception as exc:
        logger.exception("[AUTO_APPLY] post-apply tracking failed")
        await record_apply_error(session.session_id, f"Post-apply tracking failed: {exc}")


async def confirm_assisted_apply(
    session_id: str,
    body: ApplyConfirmRequest | None = None,
) -> ApplySessionDocument:
    session = await get_apply_session(session_id)
    if not session:
        raise AutoApplyError("Apply session not found")
    if session.state != "WAITING_CONFIRMATION":
        raise AutoApplyError(f"Session not awaiting confirmation (state={session.state})")

    updates: dict[str, Any] = {"confirmed": True}
    if body and body.answers:
        updates["metadata.user_answers"] = body.answers

    await update_apply_session(session_id, updates)
    signal_apply_confirm(session_id)
    await record_apply_history(session_id, "confirmed")

    return await get_apply_session(session_id) or session


async def cancel_assisted_apply(session_id: str) -> ApplySessionDocument:
    session = await get_apply_session(session_id)
    if not session:
        raise AutoApplyError("Apply session not found")

    signal_apply_cancel(session_id)
    await update_apply_session(session_id, {"state": "CANCELLED"})
    await record_apply_history(session_id, "cancelled")
    return await get_apply_session(session_id) or session


async def get_session_status(session_id: str) -> ApplySessionDocument | None:
    return await get_apply_session(session_id)
