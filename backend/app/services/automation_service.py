"""
High-level automation test flows (infrastructure only — no login or scraping).
"""

from __future__ import annotations

import logging

from app.automation.browser.executor import run_playwright
from app.automation.browser.prepare_signals import ManualSessionMode, signal_manual_done
from app.automation.browser.session_manager import normalize_platform
from app.automation.browser.session_status_service import (
    delete_session,
    get_all_sessions_status,
    is_session_ready,
)
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
)
from app.services.job_service import fetch_and_merge_linkedin_jobs

logger = logging.getLogger(__name__)


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
) -> TestSessionResponse:
    logger.info(
        "[SESSION] API prepare-session requested platform=%s",
        platform,
    )
    data = await run_playwright(
        "prepare-session",
        platform=platform,
        headless=headless,
        timeout_sec=600,
    )
    return TestSessionResponse(**data)


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


async def open_platform_session(platform: str) -> OpenSessionResponse:
    normalize_platform(platform)
    if not is_session_ready(platform):
        return OpenSessionResponse(
            status="error",
            platform=platform.lower(),
            message="No valid saved session. Prepare a session first.",
        )
    data = await run_playwright(
        "open-session",
        platform=platform,
        timeout_sec=600,
    )
    return OpenSessionResponse(**data)


def delete_platform_session(platform: str) -> DeleteSessionResponse:
    key = normalize_platform(platform)
    delete_session(key)
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


async def shutdown_automation() -> None:
    await run_playwright("close")
