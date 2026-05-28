import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.automation.browser.screenshot_service import AUTOMATION_ROOT
from app.auth.dependencies import get_current_user
from app.models.automation import (
    BrowserHealthResponse,
    DeleteSessionResponse,
    LinkedInConnectWithCodeRequest,
    LinkedInConnectWithCodeResponse,
    LinkedInConnectionStatusResponse,
    LinkedInDisconnectResponse,
    LinkedInResyncRequest,
    LinkedInResyncResponse,
    LinkedInDiscoveryResponse,
    LinkedInPairingCodeResponse,
    OpenSessionResponse,
    PrepareSessionDoneResponse,
    SessionStatusResponse,
    PlatformSessionStatus,
    TestOpenRequest,
    TestOpenResponse,
    TestSessionResponse,
)
from app.services.automation_service import (
    check_browser_health,
    confirm_open_session_done,
    confirm_prepare_session_done,
    connect_linkedin_with_pairing_code,
    delete_platform_session,
    disconnect_linkedin,
    generate_linkedin_pairing_code,
    resync_linkedin_with_token,
    get_session_status,
    get_linkedin_connection_status,
    open_platform_session,
    run_linkedin_discovery_test,
    test_open_url,
    test_platform_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["automation"])
public_router = APIRouter(tags=["automation"])


@router.get("/automation/browser-health", response_model=BrowserHealthResponse)
async def browser_health() -> BrowserHealthResponse:
    """Verify Playwright can launch Chromium."""
    return await check_browser_health()


@router.get("/automation/session-status", response_model=SessionStatusResponse)
async def session_status() -> SessionStatusResponse:
    """Per-platform session health and metadata."""
    return get_session_status()


@router.post(
    "/automation/linkedin/pairing-code",
    response_model=LinkedInPairingCodeResponse,
)
async def linkedin_pairing_code(
    _user: dict = Depends(get_current_user),
) -> LinkedInPairingCodeResponse:
    """Generate 6-digit one-time pairing code (expires in 5 minutes)."""
    try:
        return await generate_linkedin_pairing_code()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


@public_router.post(
    "/automation/linkedin/connect-with-code",
    response_model=LinkedInConnectWithCodeResponse,
)
async def connect_linkedin_with_code(
    payload: LinkedInConnectWithCodeRequest,
) -> LinkedInConnectWithCodeResponse:
    """Connect LinkedIn cookies using temporary pairing code (no JWT in extension)."""
    from app.core.extension_version import extension_version_message, extension_version_ok

    if not extension_version_ok(payload.extensionVersion):
        raise HTTPException(
            status_code=426,
            detail={"message": extension_version_message(payload.extensionVersion)},
        )
    try:
        return await connect_linkedin_with_pairing_code(
            pairing_code=payload.pairingCode,
            cookies=[cookie.model_dump() for cookie in payload.cookies],
            user_agent=payload.userAgent,
            extension_version=payload.extensionVersion,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


@public_router.post(
    "/automation/linkedin/resync",
    response_model=LinkedInResyncResponse,
)
async def resync_linkedin(payload: LinkedInResyncRequest) -> LinkedInResyncResponse:
    """Silent extension resync using stored sync token (no pairing code)."""
    from app.core.extension_version import extension_version_message, extension_version_ok

    if not extension_version_ok(payload.extensionVersion):
        raise HTTPException(
            status_code=426,
            detail={"message": extension_version_message(payload.extensionVersion)},
        )
    try:
        return await resync_linkedin_with_token(
            sync_token=payload.syncToken,
            cookies=[cookie.model_dump() for cookie in payload.cookies],
            user_agent=payload.userAgent,
            extension_version=payload.extensionVersion,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


@router.post(
    "/automation/linkedin/disconnect",
    response_model=LinkedInDisconnectResponse,
)
async def linkedin_disconnect(
    _user: dict = Depends(get_current_user),
) -> LinkedInDisconnectResponse:
    return await disconnect_linkedin()


@router.get(
    "/automation/linkedin/status",
    response_model=LinkedInConnectionStatusResponse,
)
async def linkedin_connection_status(
    _user: dict = Depends(get_current_user),
) -> LinkedInConnectionStatusResponse:
    return await get_linkedin_connection_status()


@router.delete(
    "/automation/session/{platform}",
    response_model=DeleteSessionResponse,
)
async def remove_session(platform: str) -> DeleteSessionResponse:
    """Delete session JSON and metadata for a platform."""
    try:
        return await delete_platform_session(platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.post(
    "/automation/open-session/{platform}",
    response_model=OpenSessionResponse,
)
async def open_session(platform: str) -> OpenSessionResponse:
    """
    Launch headed Chromium with saved storage state for visual verification.
    """
    try:
        result = await open_platform_session(platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    if result.status == "error":
        raise HTTPException(
            status_code=400,
            detail={"message": result.message, "platform": result.platform},
        )
    return result


@router.post(
    "/automation/linkedin-discovery",
    response_model=LinkedInDiscoveryResponse,
)
async def linkedin_discovery_test() -> LinkedInDiscoveryResponse:
    """Run read-only LinkedIn job discovery using saved session."""
    return await run_linkedin_discovery_test()


@router.post("/automation/test-open", response_model=TestOpenResponse)
async def test_open(payload: TestOpenRequest) -> TestOpenResponse:
    """Open a URL, capture a screenshot, return page metadata."""
    result = await test_open_url(
        str(payload.url),
        platform=payload.platform,
        headless=payload.headless,
    )
    if result.status == "error":
        logger.warning("[AUTOMATION][API] test-open error: %s", result.message)
    return result


@router.post(
    "/automation/test-session/{platform}",
    response_model=TestSessionResponse,
)
async def test_session(platform: str) -> TestSessionResponse:
    """
    Prepare session: headed browser, manual login, save after all tabs closed.
    """
    logger.info("[SESSION] POST /automation/test-session/%s", platform)
    try:
        result = await test_platform_session(platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    if result.status == "error":
        logger.error(
            "[SESSION] prepare-session failed platform=%s message=%s",
            platform,
            result.message,
        )
        raise HTTPException(
            status_code=502,
            detail={"message": result.message, "platform": result.platform},
        )
    return result


@router.post(
    "/automation/test-session/{platform}/done",
    response_model=PrepareSessionDoneResponse,
)
async def prepare_session_done(platform: str) -> PrepareSessionDoneResponse:
    """
    Call while prepare-session is running after the user finished logging in.

    The worker polls for this signal because Playwright cannot reliably detect
    tab/window close on Windows.
    """
    logger.info("[SESSION] POST /automation/test-session/%s/done", platform)
    try:
        return confirm_prepare_session_done(platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


@router.post(
    "/automation/open-session/{platform}/done",
    response_model=PrepareSessionDoneResponse,
)
async def open_session_done(platform: str) -> PrepareSessionDoneResponse:
    """Call while open-session is running after the user finished viewing."""
    logger.info("[SESSION] POST /automation/open-session/%s/done", platform)
    try:
        return confirm_open_session_done(platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


@router.get("/automation/screenshot/{file_path:path}")
async def serve_screenshot(file_path: str) -> FileResponse:
    """
    Serve a screenshot from automation/logs (debug UI only).

    Path must be under logs/screenshots.
    """
    normalized = file_path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise HTTPException(status_code=400, detail={"message": "Invalid path"})

    if not normalized.startswith("logs/screenshots/"):
        raise HTTPException(status_code=400, detail={"message": "Path not allowed"})

    absolute = (AUTOMATION_ROOT / normalized).resolve()
    screenshots_root = (AUTOMATION_ROOT / "logs" / "screenshots").resolve()

    try:
        absolute.relative_to(screenshots_root)
    except ValueError:
        raise HTTPException(status_code=403, detail={"message": "Access denied"}) from None

    if not absolute.is_file():
        raise HTTPException(status_code=404, detail={"message": "Screenshot not found"})

    return FileResponse(absolute, media_type="image/png")


@router.get("/automation/runtime")
async def automation_runtime() -> dict[str, bool | str]:
    """Playwright runs in isolated worker subprocesses, not inside the API process."""
    return {
        "worker_isolated": True,
        "browser_running_in_api": False,
    }
