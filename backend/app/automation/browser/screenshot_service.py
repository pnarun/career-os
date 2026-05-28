"""
Screenshot capture for automation debugging.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger(__name__)

AUTOMATION_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = AUTOMATION_ROOT / "logs" / "screenshots"
HTML_SNAPSHOTS_DIR = AUTOMATION_ROOT / "logs" / "html_snapshots"


def _platform_dir(platform: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in platform.lower())
    return SCREENSHOTS_DIR / (safe or "generic")


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def capture_page_sync(
    page: Any,
    *,
    platform: str = "generic",
    label: str = "page",
) -> Path:
    """Sync variant for thread-pool Playwright runner."""
    directory = _platform_dir(platform)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{_timestamp_slug()}_{label}.png"
    path = directory / filename
    page.screenshot(path=str(path), full_page=True)
    logger.info(
        "[AUTOMATION][SCREENSHOT] platform=%s label=%s path=%s",
        platform,
        label,
        path,
    )
    return path


def capture_error_state_sync(
    page: Any,
    *,
    platform: str = "generic",
    error_label: str = "error",
) -> Path:
    return capture_page_sync(page, platform=platform, label=f"error_{error_label}")


async def capture_page(
    page: Any,
    *,
    platform: str = "generic",
    label: str = "page",
) -> Path:
    """Capture a full-page screenshot; return absolute path."""
    directory = _platform_dir(platform)
    directory.mkdir(parents=True, exist_ok=True)

    filename = f"{_timestamp_slug()}_{label}.png"
    path = directory / filename

    await page.screenshot(path=str(path), full_page=True)
    logger.info(
        "[AUTOMATION][SCREENSHOT] platform=%s label=%s path=%s",
        platform,
        label,
        path,
    )
    return path


async def capture_error_state(
    page: Any,
    *,
    platform: str = "generic",
    error_label: str = "error",
) -> Path:
    """Capture screenshot when something failed (debug helper)."""
    return await capture_page(
        page,
        platform=platform,
        label=f"error_{error_label}",
    )


def save_html_snapshot_sync(
    page: Any,
    *,
    platform: str = "generic",
    label: str = "page",
) -> Path:
    """Persist page HTML for selector debugging (sync Playwright worker)."""
    directory = HTML_SNAPSHOTS_DIR / "".join(
        c if c.isalnum() or c in "-_" else "_" for c in platform.lower()
    ) or "generic"
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{_timestamp_slug()}_{label}.html"
    path = directory / filename
    html = page.content()
    path.write_text(html, encoding="utf-8")
    logger.info(
        "[AUTOMATION][HTML] platform=%s label=%s path=%s bytes=%d",
        platform,
        label,
        path,
        len(html.encode("utf-8")),
    )
    return path


def screenshot_relative_path(absolute: Path) -> str:
    """Path relative to automation root for API responses."""
    try:
        return str(absolute.relative_to(AUTOMATION_ROOT)).replace("\\", "/")
    except ValueError:
        return str(absolute).replace("\\", "/")
