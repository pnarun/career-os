"""User-facing automation error messages (hide raw Playwright tracebacks)."""

from __future__ import annotations

import os
import sys


def assert_headed_browser_available() -> None:
    """Prepare/open session need a visible browser — not on headless cloud hosts."""
    if sys.platform in ("win32", "darwin"):
        return
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return
    if os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"):
        raise RuntimeError(
            "Session prepare must run on your local machine (backend on localhost), "
            "not on Render/cloud. Point the app at your local API with "
            "PLAYWRIGHT_HEADLESS=false."
        )
    raise RuntimeError(
        "No graphical display detected (DISPLAY/WAYLAND). "
        "Run the Career OS backend locally on Windows/macOS, or on Linux with a "
        "desktop session or xvfb-run."
    )


def user_facing_automation_error(exc: BaseException) -> str:
    msg = str(exc).strip()
    lower = msg.lower()

    if "session prepare must run" in lower or "no graphical display" in lower:
        return msg

    if "executable doesn't exist" in lower or "playwright install" in lower:
        return (
            "Playwright Chromium is not installed. In the backend folder run: "
            "playwright install chromium"
        )

    if "target page, context or browser has been closed" in lower:
        return (
            "Chromium closed during launch. Close other automation browsers, then retry. "
            "If this persists, restart the backend and run playwright install chromium."
        )

    if "dbus" in lower or "display" in lower or "ozone" in lower:
        return (
            "Cannot open a visible browser in this environment. "
            "Use a local backend on Windows/macOS with PLAYWRIGHT_HEADLESS=false."
        )

    if "timeout" in lower and "exceeded" in lower:
        return msg.split("\n")[0][:400]

    first_line = msg.split("\n")[0].strip()
    if len(first_line) > 400:
        first_line = first_line[:397] + "..."
    return first_line or "Session automation failed"
