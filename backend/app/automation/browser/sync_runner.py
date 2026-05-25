"""
Synchronous Playwright runner executed in a dedicated worker thread.

Browser I/O must not run on uvicorn's ProactorEventLoop (Windows).
"""

from __future__ import annotations

import logging
import random
import time
import traceback
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext

from app.automation.browser.screenshot_service import (
    capture_error_state_sync,
    capture_page_sync,
    screenshot_relative_path,
)
from app.automation.browser.session_manager import (
    get_platform_home_url,
    load_session,
    normalize_platform,
    session_exists,
    _session_path,
)
from app.automation.session_logging import session_log, session_log_traceback
from app.automation.browser.session_status_service import (
    is_session_ready,
    refresh_session_metadata,
)

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_playwright: Any = None
_browser: Any = None


def _settings():
    from app.core.config import settings

    return settings


def _viewport() -> dict[str, int]:
    s = _settings()
    return {
        "width": s.PLAYWRIGHT_VIEWPORT_WIDTH,
        "height": s.PLAYWRIGHT_VIEWPORT_HEIGHT,
    }


def _user_agent() -> str:
    return _settings().PLAYWRIGHT_USER_AGENT or DEFAULT_USER_AGENT


def _launch_headless(override: bool | None) -> bool:
    return _settings().PLAYWRIGHT_HEADLESS if override is None else override


def _human_delay(min_ms: float, max_ms: float) -> None:
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)


def _ensure_browser(headless: bool | None = None, *, trace_session: bool = False) -> Any:
    global _playwright, _browser
    from playwright.sync_api import sync_playwright

    def _log(msg: str) -> None:
        if trace_session:
            session_log(msg)

    if _browser is not None and _browser.is_connected():
        _log("[SESSION] Reusing existing Chromium connection")
        return _browser

    _log("[SESSION] No active browser — closing prior Playwright driver if any")
    close_browser_sync(trace_session=trace_session)

    launch_headless = _launch_headless(headless)
    _log(f"[SESSION] Starting Playwright driver (headless={launch_headless})")
    logger.info("[AUTOMATION][BROWSER] launching chromium headless=%s", launch_headless)
    _playwright = sync_playwright().start()
    _log("[SESSION] Playwright driver started")

    slow_mo = _settings().PLAYWRIGHT_SLOW_MO
    _log("[SESSION] Launching Chromium process")
    _browser = _playwright.chromium.launch(
        headless=launch_headless,
        slow_mo=slow_mo if slow_mo > 0 else None,
    )
    _log(f"[SESSION] Chromium launched connected={_browser.is_connected()}")
    logger.info("[AUTOMATION][BROWSER] chromium ready")
    return _browser


def close_browser_sync(*, trace_session: bool = False) -> None:
    global _playwright, _browser

    def _log(msg: str) -> None:
        if trace_session:
            session_log(msg)

    if _browser is not None:
        try:
            if _browser.is_connected():
                _log("[SESSION] Closing Chromium browser")
                _browser.close()
            logger.info("[AUTOMATION][BROWSER] closed")
        except Exception as exc:
            err = str(exc).lower()
            if trace_session and (
                "closed" in err or "connection" in err or "disposed" in err
            ):
                _log("[SESSION] Browser already closed (ignored)")
            else:
                if trace_session:
                    session_log_traceback("close_browser_sync.browser.close")
                logger.exception("[AUTOMATION][BROWSER] error during browser close")
        finally:
            _browser = None

    if _playwright is not None:
        try:
            _log("[SESSION] Stopping Playwright driver")
            _playwright.stop()
            logger.info("[AUTOMATION][BROWSER] playwright stopped")
        except Exception:
            if trace_session:
                session_log_traceback("close_browser_sync.playwright.stop")
            logger.exception("[AUTOMATION][BROWSER] error during playwright stop")
        finally:
            _playwright = None


def browser_is_running_sync() -> bool:
    return _browser is not None and _browser.is_connected()


def create_context_sync(
    *,
    platform: str | None = None,
    headless: bool | None = None,
    use_saved_session: bool = False,
    trace_session: bool = False,
) -> Any:
    def _log(msg: str) -> None:
        if trace_session:
            session_log(msg)

    _log("[SESSION] create_context_sync — acquiring browser")
    browser = _ensure_browser(headless, trace_session=trace_session)

    options: dict[str, Any] = {
        "viewport": _viewport(),
        "user_agent": _user_agent(),
        "locale": "en-US",
        "timezone_id": "Asia/Kolkata",
        "accept_downloads": False,
    }

    storage_state = None
    if use_saved_session and platform:
        _log(f"[SESSION] Loading saved storage state for platform={platform}")
        storage_state = load_session(platform)
        _log(
            "[SESSION] Storage state loaded"
            if storage_state
            else "[SESSION] No storage state file to load"
        )
    if storage_state is not None:
        options["storage_state"] = storage_state

    _log("[SESSION] Creating browser context")
    context = browser.new_context(**options)
    timeout_ms = _settings().PLAYWRIGHT_DEFAULT_TIMEOUT_MS
    context.set_default_timeout(timeout_ms)
    context.set_default_navigation_timeout(timeout_ms)
    _log("[SESSION] Context created")
    return context


def check_browser_health_sync() -> dict[str, Any]:
    try:
        browser = _ensure_browser()
        version = browser.version
        connected = browser.is_connected()
        close_browser_sync()
        if connected:
            return {
                "status": "ok",
                "browser_connected": True,
                "chromium_version": version,
                "message": "Chromium launched and shut down successfully.",
            }
        return {
            "status": "degraded",
            "browser_connected": False,
            "chromium_version": version,
            "message": "Browser launched but was not connected.",
        }
    except Exception as exc:
        logger.exception("[AUTOMATION][HEALTH] failed")
        close_browser_sync()
        return {
            "status": "error",
            "browser_connected": False,
            "chromium_version": "",
            "message": str(exc) or repr(exc),
        }


def test_open_url_sync(
    url: str,
    *,
    platform: str = "generic",
    headless: bool | None = None,
) -> dict[str, Any]:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    context = None
    page = None
    try:
        context = create_context_sync(platform=platform, headless=headless)
        page = context.new_page()
        _human_delay(200, 400)

        response = page.goto(url, wait_until="domcontentloaded")
        _human_delay(300, 600)

        title = page.title()
        screenshot = capture_page_sync(page, platform=platform, label="test_open")
        rel_path = screenshot_relative_path(screenshot)
        status_code = response.status if response else 0
        status = "ok" if status_code < 400 else "warning"

        return {
            "status": status,
            "title": title,
            "screenshot_path": rel_path,
            "url": page.url,
            "message": f"Page loaded (HTTP {status_code}).",
        }
    except PlaywrightTimeoutError as exc:
        rel_path = ""
        if page is not None:
            try:
                shot = capture_error_state_sync(page, platform=platform, error_label="timeout")
                rel_path = screenshot_relative_path(shot)
            except Exception:
                logger.exception("[AUTOMATION][TEST_OPEN] screenshot on timeout failed")
        return {
            "status": "error",
            "title": page.title() if page else "",
            "screenshot_path": rel_path,
            "url": page.url if page else url,
            "message": f"Navigation timeout: {exc}",
        }
    except Exception as exc:
        logger.exception("[AUTOMATION][TEST_OPEN] failed url=%s", url)
        rel_path = ""
        if page is not None:
            try:
                shot = capture_error_state_sync(page, platform=platform, error_label="failure")
                rel_path = screenshot_relative_path(shot)
            except Exception:
                pass
        return {
            "status": "error",
            "title": page.title() if page else "",
            "screenshot_path": rel_path,
            "url": page.url if page else url,
            "message": str(exc),
        }
    finally:
        if context is not None:
            context.close()


PREPARE_SESSION_MAX_WAIT_SEC = 600
# Do not treat "all pages closed" until login window had time to open (avoids instant exit).
MANUAL_WAIT_GRACE_SEC = 5


def _collect_contexts(browser, tracked_context: Any | None) -> list[Any]:
    """Merge tracked context with browser.contexts (Playwright may omit the latter)."""
    contexts: list[Any] = []
    seen: set[int] = set()

    if tracked_context is not None:
        contexts.append(tracked_context)
        seen.add(id(tracked_context))

    if browser is not None:
        try:
            for ctx in browser.contexts:
                if id(ctx) not in seen:
                    contexts.append(ctx)
                    seen.add(id(ctx))
        except Exception:
            pass

    return contexts


# Leftover tabs Playwright/Chromium keep after the user closes visible UI.
_IGNORABLE_PAGE_URLS = frozenset({
    "",
    "about:blank",
    "chrome://newtab/",
    "chrome://new-tab-page/",
    "chrome://welcome/",
})


def _page_url(page: Any) -> str:
    try:
        return page.url or ""
    except Exception:
        return ""


def _is_page_closed(page: Any) -> bool:
    try:
        return page.is_closed()
    except Exception:
        return True


def _is_ignorable_residual_page(page: Any) -> bool:
    """about:blank / new-tab shells that remain after the user closes Chromium UI."""
    url = _page_url(page).strip().lower()
    if url in _IGNORABLE_PAGE_URLS:
        return True
    if url.startswith("about:blank"):
        return True
    if url.startswith("chrome://newtab"):
        return True
    return False


def _page_is_open_in_context(page: Any, context: Any | None) -> bool:
    """False when the tab was closed in Chromium (even if is_closed() lags)."""
    if _is_page_closed(page):
        return False
    if context is None:
        return True
    try:
        return page in context.pages
    except Exception:
        return False


def _raw_page_count(browser, tracked_context: Any | None) -> int:
    total = 0
    for ctx in _collect_contexts(browser, tracked_context):
        try:
            total += len(ctx.pages)
        except Exception:
            continue
    return total


def _browser_is_connected(browser: Any | None) -> bool:
    if browser is None:
        return False
    try:
        return browser.is_connected()
    except Exception:
        return False


def _manual_wait_complete(
    browser,
    tracked_context: Any | None,
    main_page: Any | None,
    *,
    platform: str | None = None,
    done_mode: str | None = None,
    user_done: dict[str, Any],
) -> tuple[bool, str]:
    """
    Decide whether the user finished login and closed the browser UI.

    Prefer the UI Done button — Playwright often keeps stale pages when only
    the tab is closed on Windows.
    """
    if platform and done_mode:
        from app.automation.browser.prepare_signals import is_manual_done

        if is_manual_done(platform, done_mode):
            return True, "user_clicked_done_in_ui"

    if user_done.get("flag"):
        return True, str(user_done.get("reason") or "event")

    if browser is not None and not _browser_is_connected(browser):
        return True, "browser_disconnected"

    if _raw_page_count(browser, tracked_context) == 0:
        return True, "no_pages_in_context"

    if main_page is not None:
        if _is_page_closed(main_page):
            return True, "main_page_is_closed"
        if not _page_is_open_in_context(main_page, tracked_context):
            return True, "main_page_removed_from_context"

    open_real_pages = 0
    for ctx in _collect_contexts(browser, tracked_context):
        try:
            for page in ctx.pages:
                if not _page_is_open_in_context(page, ctx):
                    continue
                if _is_ignorable_residual_page(page):
                    continue
                open_real_pages += 1
        except Exception:
            continue

    if open_real_pages == 0:
        return True, "only_blank_or_closed_pages"

    return False, ""


def _log_manual_wait_snapshot(
    browser,
    tracked_context: Any | None,
    main_page: Any | None,
) -> None:
    connected = _browser_is_connected(browser)
    raw = _raw_page_count(browser, tracked_context)
    session_log(
        f"[SESSION] browser.is_connected()={connected} raw_pages={raw}"
    )

    if main_page is not None:
        in_ctx = _page_is_open_in_context(main_page, tracked_context)
        session_log(
            f"[SESSION] main_page url={_page_url(main_page)!r} "
            f"closed={_is_page_closed(main_page)} in_context={in_ctx}"
        )

    contexts = _collect_contexts(browser, tracked_context)
    for ctx_idx, ctx in enumerate(contexts):
        try:
            pages = list(ctx.pages)
        except Exception as exc:
            session_log(f"[SESSION] Context {ctx_idx} error={exc}")
            continue
        for page_idx, page in enumerate(pages):
            session_log(
                f"[SESSION] Context {ctx_idx} page {page_idx}: "
                f"url={_page_url(page)!r} closed={_is_page_closed(page)} "
                f"in_ctx={_page_is_open_in_context(page, ctx)} "
                f"ignorable={_is_ignorable_residual_page(page)}"
            )


def _wait_for_all_pages_closed(
    browser,
    tracked_context: Any | None = None,
    *,
    main_page: Any | None = None,
    platform: str | None = None,
    done_mode: str | None = "prepare",
    max_wait_sec: int = PREPARE_SESSION_MAX_WAIT_SEC,
) -> bool:
    """
    Poll until the user signals done (UI button) or closes the browser.

    Returns True if max_wait_sec elapsed before completion.
    """
    done_hint = (
        "'Done logging in'"
        if done_mode == "prepare"
        else "'Done viewing session'"
    )
    session_log(
        f"[SESSION] Entered manual wait loop — click {done_hint} "
        "in the Automation page (or close the Chromium window)"
    )
    started = time.monotonic()
    timed_out = False
    user_done: dict[str, Any] = {"flag": False, "reason": ""}

    def _mark_done(reason: str) -> None:
        if not user_done["flag"]:
            user_done["flag"] = True
            user_done["reason"] = reason
            session_log(f"[SESSION] User done signal: {reason}")

    if browser is not None:
        try:
            browser.on("disconnected", lambda: _mark_done("browser_disconnected_event"))
        except Exception:
            pass

    if main_page is not None:
        try:
            main_page.on("close", lambda: _mark_done("main_page_close_event"))
        except Exception:
            pass

    poll_interval = 2.0
    last_log = 0.0

    while True:
        elapsed = time.monotonic() - started
        complete, reason = _manual_wait_complete(
            browser,
            tracked_context,
            main_page,
            platform=platform,
            done_mode=done_mode,
            user_done=user_done,
        )

        if elapsed - last_log >= 5.0:
            _log_manual_wait_snapshot(browser, tracked_context, main_page)
            last_log = elapsed

        if elapsed >= MANUAL_WAIT_GRACE_SEC and complete:
            session_log(f"[SESSION] Manual wait complete ({reason})")
            break

        if elapsed >= max_wait_sec:
            timed_out = True
            session_log(
                f"[SESSION] Prepare session timed out after {max_wait_sec}s — "
                "close the Chromium window (X) to save, not just the tab"
            )
            break

        time.sleep(poll_interval)

    return timed_out


def _context_has_cookies(context) -> bool:
    """Check in-memory storage state for cookies (used on timeout fallback)."""
    if context is None:
        return False
    state = context.storage_state()
    cookies = state.get("cookies") if isinstance(state, dict) else []
    return isinstance(cookies, list) and len(cookies) > 0


def prepare_platform_session_sync(
    platform: str,
    *,
    headless: bool | None = None,
) -> dict[str, Any]:
    """
    Open headed browser for manual login; save storage state only after user closes it.
    """
    session_log(f"[SESSION] prepare_platform_session_sync started platform={platform}")
    context = None
    browser = None
    page = None
    home_url = ""
    key = ""
    session_path = None
    state_saved = {"done": False}
    timed_out = False

    def _persist_storage_state() -> bool:
        if state_saved["done"] or context is None:
            return state_saved["done"]
        session_log(f"[SESSION] Writing storage_state to {session_path}")
        session_path.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(session_path))
        state_saved["done"] = True
        session_log(
            f"[SESSION] Storage state saved platform={key} path={session_path}"
        )
        return True

    try:
        from app.automation.browser.prepare_signals import clear_manual_done

        _ = headless
        session_log("[SESSION] Resolving platform URL")
        home_url = get_platform_home_url(platform)
        key = normalize_platform(platform)
        clear_manual_done(key, "prepare")
        session_path = _session_path(key)
        session_log(f"[SESSION] Platform={key} home_url={home_url}")

        session_log("[SESSION] Launching Chromium")
        browser = _ensure_browser(headless=False, trace_session=True)
        session_log("[SESSION] Chromium launched")

        session_log("[SESSION] Creating context")
        context = create_context_sync(
            platform=platform,
            headless=False,
            trace_session=True,
        )
        session_log("[SESSION] Context created")

        session_log("[SESSION] Creating page")
        page = context.new_page()
        session_log(f"[SESSION] Page created (pages in context={len(context.pages)})")

        session_log("[SESSION] Brief delay before navigation")
        _human_delay(250, 500)

        session_log(f"[SESSION] Navigating to platform URL: {home_url}")
        response = page.goto(home_url, wait_until="domcontentloaded", timeout=60_000)
        status = response.status if response else "no-response"
        session_log(f"[SESSION] Navigation complete status={status} current_url={page.url}")

        session_log(
            f"[SESSION] Browser ready — log in, then close the Chromium window "
            f"(platform={key})"
        )
        timed_out = _wait_for_all_pages_closed(
            browser, context, main_page=page, platform=key, done_mode="prepare"
        )

        from app.automation.browser.prepare_signals import consume_manual_done

        if consume_manual_done(key, "prepare"):
            session_log("[SESSION] Consumed UI prepare-done signal")

        session_log("[SESSION] Saving authenticated session")
        _persist_storage_state()

        if not state_saved["done"] and timed_out and _context_has_cookies(context):
            session_log("[SESSION] Retrying save after timeout (cookies present)")
            _persist_storage_state()

        if not state_saved["done"]:
            err_msg = (
                "Could not save session after browser close."
                if not timed_out
                else "Prepare session timed out and storage state could not be saved."
            )
            session_log(f"[SESSION] ERROR: {err_msg}")
            return {
                "status": "error",
                "platform": key,
                "session_saved": session_exists(platform),
                "session_path": "",
                "home_url": home_url,
                "message": err_msg,
            }

        session_log("[SESSION] Refreshing session metadata")
        meta = refresh_session_metadata(platform)
        login_warning = (
            meta.get("cookie_count", 0) < 5 or meta.get("storage_size_kb", 0) < 3
        )
        if login_warning:
            session_log(
                f"[SESSION] WARNING: session may be incomplete cookies={meta.get('cookie_count')} "
                f"size_kb={meta.get('storage_size_kb')}"
            )

        if timed_out:
            message = (
                "Session saved after timeout (10 min). Close all browser tabs sooner next time."
                if not login_warning
                else (
                    "Session saved after timeout, but it may be incomplete — "
                    "log in fully before closing the browser."
                )
            )
            login_warning = True
        elif login_warning:
            message = (
                "Session saved, but it looks incomplete — log in fully before closing "
                "the browser next time."
            )
        else:
            message = "Session saved after you closed the browser."

        session_log(f"[SESSION] prepare_platform_session_sync success: {message}")
        return {
            "status": "ok",
            "platform": key,
            "session_saved": True,
            "session_path": f"profiles/{key}_session.json",
            "home_url": home_url,
            "session_status": meta.get("status", "none"),
            "cookie_count": meta.get("cookie_count", 0),
            "storage_size_kb": meta.get("storage_size_kb", 0),
            "last_saved_at": meta.get("last_saved_at"),
            "login_warning": login_warning,
            "message": message,
        }
    except Exception as exc:
        tb = traceback.format_exc()
        session_log(f"[SESSION] prepare_platform_session_sync FAILED: {exc}")
        session_log(f"[SESSION] TRACEBACK:\n{tb}")
        logger.exception("[AUTOMATION][PREPARE_SESSION] platform=%s failed", platform)
        return {
            "status": "error",
            "platform": key or platform.lower(),
            "session_saved": session_exists(platform) if key else False,
            "session_path": "",
            "home_url": home_url,
            "message": f"{exc}\n\n{tb}",
        }
    finally:
        session_log("[SESSION] finally: closing browser")
        close_browser_sync(trace_session=True)
        session_log("[SESSION] finally: browser close complete")


# Python import alias only — worker subprocess uses prepare-session command.
test_platform_session_sync = prepare_platform_session_sync


def open_session_sync(platform: str) -> dict[str, Any]:
    """
    Launch headed Chromium with saved storage state for visual verification.

    Blocks until the user closes the browser window.
    """
    key = normalize_platform(platform)
    home_url = get_platform_home_url(platform)

    if not is_session_ready(platform):
        return {
            "status": "error",
            "platform": key,
            "message": "No valid saved session. Prepare a session first.",
        }

    context = None
    browser = None
    page = None
    try:
        from app.automation.browser.prepare_signals import (
            clear_manual_done,
            consume_manual_done,
        )

        clear_manual_done(key, "open")
        browser = _ensure_browser(headless=False)
        context = create_context_sync(
            platform=platform,
            headless=False,
            use_saved_session=True,
        )
        page = context.new_page()
        _human_delay(300, 500)
        page.goto(home_url, wait_until="domcontentloaded", timeout=60_000)

        logger.info(
            "[AUTOMATION][OPEN_SESSION] platform=%s headed browser open",
            key,
        )

        _wait_for_all_pages_closed(
            browser, context, main_page=page, platform=key, done_mode="open"
        )
        if consume_manual_done(key, "open"):
            session_log("[SESSION] Consumed UI open-session-done signal")

        return {
            "status": "ok",
            "platform": key,
            "home_url": home_url,
            "message": "Browser launched with saved session.",
        }
    except Exception as exc:
        logger.exception("[AUTOMATION][OPEN_SESSION] platform=%s failed", platform)
        return {
            "status": "error",
            "platform": key,
            "message": str(exc),
        }
    finally:
        if context is not None:
            context.close()
        close_browser_sync()
