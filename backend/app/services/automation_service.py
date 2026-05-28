"""
High-level automation test flows (infrastructure only — no login or scraping).
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from app.automation.browser.executor import run_playwright
from app.automation.browser.prepare_signals import ManualSessionMode, signal_manual_done
from app.automation.browser.session_manager import normalize_platform
from app.automation.browser.session_status_service import (
    delete_session,
    get_all_sessions_status,
    is_session_ready,
)
from app.core.config import settings
from app.core.user_context import require_request_user_id
from app.models.automation import (
    BrowserHealthResponse,
    DeleteSessionResponse,
    LinkedInDiscoveryResponse,
    OpenSessionResponse,
    PlatformSessionStatus,
    SessionStatusResponse,
    PrepareSessionDoneResponse,
    TestOpenResponse,
    TestSessionResponse,
    LinkedInConnectionStatusResponse,
    LinkedInConnectWithCodeResponse,
    LinkedInDisconnectResponse,
    LinkedInPairingCodeResponse,
    LinkedInResyncResponse,
)
from app.core.database import get_database
from app.services.browser_session_store import (
    delete_storage_state,
    find_user_id_by_extension_sync_token,
    get_session_info,
    save_storage_state,
)
from app.services.job_service import fetch_and_merge_linkedin_jobs
from app.services.linkedin_pairing_service import (
    create_pairing_code,
    invalidate_pairing_sessions_for_user,
    redeem_pairing_code,
)

LINKEDIN_SESSION_STALE_DAYS = 14
JOBS_COLLECTION = "jobs"

logger = logging.getLogger(__name__)

_prepare_lock = asyncio.Lock()
_active_prepare: set[str] = set()
_active_open: set[str] = set()


async def check_browser_health() -> BrowserHealthResponse:
    data = await run_playwright("health")
    return BrowserHealthResponse(**data)


async def test_open_url(
    url: str,
    *,
    platform: str = "generic",
    headless: bool | None = None,
) -> TestOpenResponse:
    data = await run_playwright(
        "test-open",
        url=url,
        platform=platform,
        headless=headless,
    )
    return TestOpenResponse(**data)


async def test_platform_session(
    platform: str,
    *,
    headless: bool | None = None,
    user_id: str | None = None,
) -> TestSessionResponse:
    key = normalize_platform(platform)
    uid = user_id or require_request_user_id()
    if not settings.headed_session_prep_available:
        return TestSessionResponse(
            status="error",
            platform=key,
            session_saved=False,
            session_path="",
            home_url="",
            message=(
                "Prepare session needs a visible browser on the machine running the API. "
                "In production, use the Career Lens Chrome extension to sync LinkedIn auth."
            ),
        )
    if key in _active_prepare:
        return TestSessionResponse(
            status="error",
            platform=key,
            session_saved=False,
            session_path="",
            home_url="",
            message=(
                f"A prepare session for {key} is already running. "
                "Finish logging in and click Done, or wait for it to complete."
            ),
        )

    logger.info(
        "[SESSION] API prepare-session requested platform=%s",
        platform,
    )
    async with _prepare_lock:
        _active_prepare.add(key)
        try:
            data = await run_playwright(
                "prepare-session",
                platform=platform,
                user_id=uid,
                headless=headless,
                timeout_sec=600,
            )
            return TestSessionResponse(**data)
        finally:
            _active_prepare.discard(key)


def confirm_manual_session_done(
    platform: str,
    mode: ManualSessionMode,
) -> PrepareSessionDoneResponse:
    """User clicked Done in the UI while a headed worker is waiting."""
    key = normalize_platform(platform)
    signal_manual_done(key, mode)
    logger.info("[SESSION] manual-done signal platform=%s mode=%s", key, mode)
    if mode == "open":
        message = "Signal sent. Closing browser…"
    else:
        message = "Signal sent. Saving session and closing browser…"
    return PrepareSessionDoneResponse(
        status="ok",
        platform=key,
        message=message,
    )


def confirm_prepare_session_done(platform: str) -> PrepareSessionDoneResponse:
    return confirm_manual_session_done(platform, "prepare")


def confirm_open_session_done(platform: str) -> PrepareSessionDoneResponse:
    return confirm_manual_session_done(platform, "open")


async def open_platform_session(
    platform: str,
    *,
    user_id: str | None = None,
) -> OpenSessionResponse:
    key = normalize_platform(platform)
    uid = user_id or require_request_user_id()
    if not is_session_ready(platform, user_id=uid):
        return OpenSessionResponse(
            status="error",
            platform=key,
            message="No valid saved session. Prepare a session first.",
        )
    if key in _active_open:
        return OpenSessionResponse(
            status="error",
            platform=key,
            message=f"An open-session for {key} is already running.",
        )

    async with _prepare_lock:
        _active_open.add(key)
        try:
            data = await run_playwright(
                "open-session",
                platform=platform,
                user_id=uid,
                timeout_sec=600,
            )
            return OpenSessionResponse(**data)
        finally:
            _active_open.discard(key)


async def delete_platform_session(platform: str) -> DeleteSessionResponse:
    key = normalize_platform(platform)
    await delete_session(key)
    return DeleteSessionResponse(
        status="ok",
        platform=key,
        message=f"Session for {key} deleted.",
    )


def get_session_status() -> SessionStatusResponse:
    raw = get_all_sessions_status()
    sessions = {
        platform: PlatformSessionStatus(**info)
        for platform, info in raw.items()
    }
    return SessionStatusResponse(sessions=sessions)


async def run_linkedin_discovery_test() -> LinkedInDiscoveryResponse:
    """Legacy automation route — delegates to headless jobs pipeline."""
    result = await fetch_and_merge_linkedin_jobs()
    return LinkedInDiscoveryResponse(
        status=result.status,
        message=result.message,
        jobs_fetched=result.jobs_fetched,
        easy_apply_count=result.easy_apply_count,
        screenshot_path="",
        session_valid=result.session_valid,
        jobs=[
            {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "url": job.apply_url,
                "apply_url": job.apply_url,
                "easy_apply": job.easy_apply,
                "source": job.source,
            }
            for job in result.jobs
        ],
    )


def _normalize_linkedin_cookie(cookie: dict) -> dict | None:
    name = str(cookie.get("name") or "").strip()
    value = str(cookie.get("value") or "")
    domain = str(cookie.get("domain") or "").strip().lower()
    if not name or not value or "linkedin.com" not in domain:
        return None

    if not domain.startswith("."):
        domain = f".{domain.lstrip('.')}"

    expires_raw = cookie.get("expires", -1)
    try:
        expires = float(expires_raw if expires_raw is not None else -1)
    except (TypeError, ValueError):
        expires = -1

    # Playwright rejects expired cookies — keep session cookies and li_at.
    if expires > 0 and expires < time.time() and name.lower() != "li_at":
        return None

    same_site_raw = (cookie.get("sameSite") or "").strip().lower()
    same_site = "Lax"
    if same_site_raw in {"none", "no_restriction"}:
        same_site = "None"
    elif same_site_raw in {"strict"}:
        same_site = "Strict"
    elif same_site_raw in {"lax", "unspecified"}:
        same_site = "Lax"

    secure = bool(cookie.get("secure", True))
    if same_site == "None":
        secure = True

    return {
        "name": name,
        "value": value,
        "domain": domain,
        "path": str(cookie.get("path") or "/") or "/",
        "expires": expires,
        "httpOnly": bool(cookie.get("httpOnly", False)),
        "secure": secure,
        "sameSite": same_site,
    }


async def _linkedin_last_fetch_meta(*, user_id: str) -> tuple[str | None, int]:
    col = get_database()[JOBS_COLLECTION]
    latest = await col.find_one(
        {"user_id": user_id, "source": "linkedin"},
        sort=[("created_at", -1)],
        projection={"created_at": 1, "scan_id": 1},
    )
    if not latest:
        return None, 0
    last_at = latest.get("created_at")
    scan_id = latest.get("scan_id")
    if scan_id:
        count = await col.count_documents(
            {"user_id": user_id, "source": "linkedin", "scan_id": scan_id}
        )
        return str(last_at) if last_at else None, int(count)
    return str(last_at) if last_at else None, 1


def _days_since_iso(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        then = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - then
        return max(0, delta.days)
    except (TypeError, ValueError):
        return None


async def connect_linkedin_session(
    *,
    cookies: list[dict],
    user_agent: str = "",
    synced_at: str | None = None,
    user_id: str | None = None,
) -> tuple[PlatformSessionStatus, str]:
    uid = user_id or require_request_user_id()
    normalized: list[dict] = []
    for cookie in cookies:
        if not cookie.get("domain") or "linkedin.com" not in str(cookie.get("domain")).lower():
            continue
        entry = _normalize_linkedin_cookie(cookie)
        if entry:
            normalized.append(entry)
    if not normalized:
        raise ValueError("No valid LinkedIn cookies found. Please log into LinkedIn first.")
    if not any(c.get("name", "").lower() == "li_at" for c in normalized):
        raise ValueError(
            "LinkedIn auth cookie (li_at) missing. Log into LinkedIn and resync from the extension."
        )
    storage_state = {"cookies": normalized, "origins": []}
    saved = await save_storage_state(
        user_id=uid,
        platform="linkedin",
        storage_state=storage_state,
        user_agent=user_agent,
        session_source="career_lens_extension",
    )
    logger.info(
        "[LINKEDIN_CONNECT] user=%s cookies=%s user_agent_present=%s synced_at=%s",
        uid,
        len(normalized),
        bool(user_agent.strip()),
        bool(synced_at),
    )
    info = await get_session_info(user_id=uid, platform="linkedin")
    result = PlatformSessionStatus(**info)
    return result, saved.get("extension_sync_token", "")


async def generate_linkedin_pairing_code(
    *,
    user_id: str | None = None,
) -> LinkedInPairingCodeResponse:
    uid = user_id or require_request_user_id()
    payload = await create_pairing_code(user_id=uid)
    return LinkedInPairingCodeResponse(
        pairingCode=str(payload["pairing_code"]),
        expiresIn=int(payload["expires_in"]),
        expiresAt=payload.get("expires_at"),
    )


async def connect_linkedin_with_pairing_code(
    *,
    pairing_code: str,
    cookies: list[dict],
    user_agent: str = "",
    extension_version: str = "",
) -> LinkedInConnectWithCodeResponse:
    redeemed = await redeem_pairing_code(
        pairing_code=pairing_code,
        extension_version=extension_version,
    )
    _status, sync_token = await connect_linkedin_session(
        cookies=cookies,
        user_agent=user_agent,
        synced_at=redeemed.get("used_at"),
        user_id=redeemed.get("user_id") or "",
    )
    synced_at = datetime.now(timezone.utc).isoformat()
    return LinkedInConnectWithCodeResponse(
        success=True,
        connected=True,
        syncedAt=synced_at,
        syncToken=sync_token,
    )


async def resync_linkedin_with_token(
    *,
    sync_token: str,
    cookies: list[dict],
    user_agent: str = "",
    extension_version: str = "",
) -> LinkedInResyncResponse:
    uid = await find_user_id_by_extension_sync_token(sync_token)
    if not uid:
        raise ValueError("Invalid or expired extension sync token. Reconnect with a pairing code.")
    _status, _token = await connect_linkedin_session(
        cookies=cookies,
        user_agent=user_agent,
        user_id=uid,
    )
    logger.info(
        "[LINKEDIN_RESYNC] user=%s extension_version=%s",
        uid,
        (extension_version or "").strip() or "unknown",
    )
    return LinkedInResyncResponse(
        success=True,
        syncedAt=datetime.now(timezone.utc).isoformat(),
    )


async def disconnect_linkedin(*, user_id: str | None = None) -> LinkedInDisconnectResponse:
    uid = user_id or require_request_user_id()
    await delete_storage_state(user_id=uid, platform="linkedin")
    await invalidate_pairing_sessions_for_user(user_id=uid)
    logger.info("[LINKEDIN_DISCONNECT] user=%s", uid)
    return LinkedInDisconnectResponse(
        success=True,
        message="LinkedIn session disconnected.",
    )


async def get_linkedin_connection_status(
    *,
    user_id: str | None = None,
) -> LinkedInConnectionStatusResponse:
    uid = user_id or require_request_user_id()
    info = await get_session_info(user_id=uid, platform="linkedin")
    connected = info.get("status") == "ready" and bool(info.get("exists"))
    last_synced = info.get("last_saved_at")
    days_since = _days_since_iso(last_synced)
    expires_soon = (
        not connected
        or info.get("status") == "corrupted"
        or (days_since is not None and days_since >= LINKEDIN_SESSION_STALE_DAYS)
    )
    session_healthy = connected and not expires_soon
    if not connected:
        provider_status = "disconnected"
    elif session_healthy:
        provider_status = "ready"
    else:
        provider_status = "degraded"

    last_fetch_at, last_fetch_count = await _linkedin_last_fetch_meta(user_id=uid)

    return LinkedInConnectionStatusResponse(
        connected=connected,
        lastSyncedAt=last_synced,
        expiresSoon=expires_soon,
        sessionHealthy=session_healthy,
        providerStatus=provider_status,
        lastFetchAt=last_fetch_at,
        lastFetchJobCount=last_fetch_count,
    )


async def shutdown_automation() -> None:
    await run_playwright("close")
