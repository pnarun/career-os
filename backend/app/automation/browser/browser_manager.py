"""
Async facade over the sync Playwright runner (see sync_runner.py + executor.py).
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext


async def get_browser(*, headless: bool | None = None):
    """Launch is handled inside create_context_sync / health checks."""
    from app.automation.browser.executor import run_playwright
    from app.automation.browser.sync_runner import _ensure_browser

    return await run_playwright(_ensure_browser, headless)


async def create_context(
    *,
    platform: str | None = None,
    headless: bool | None = None,
    storage_state: dict[str, Any] | str | None = None,
    use_saved_session: bool = False,
) -> Any:
    """Deprecated for direct use — prefer automation_service flows."""
    from app.automation.browser.executor import run_playwright
    from app.automation.browser.sync_runner import create_context_sync

    _ = storage_state
    return await run_playwright(
        create_context_sync,
        platform=platform,
        headless=headless,
        use_saved_session=use_saved_session,
    )


async def close_browser() -> None:
    from app.automation.browser.executor import run_playwright
    from app.automation.browser.sync_runner import close_browser_sync

    await run_playwright(close_browser_sync)


def browser_is_running() -> bool:
    from app.automation.browser.sync_runner import browser_is_running_sync

    return browser_is_running_sync()
