"""CAPTCHA detection — stop immediately, never bypass."""

from __future__ import annotations

from typing import Any

CAPTCHA_HINTS = (
    "captcha",
    "security verification",
    "let's do a quick security check",
    "unusual activity",
    "verify you're a human",
    "recaptcha",
    "hcaptcha",
    "challenge-platform",
)

CAPTCHA_SELECTORS = (
    "iframe[src*='captcha']",
    "iframe[src*='recaptcha']",
    "iframe[src*='hcaptcha']",
    "#captcha",
    ".captcha",
    "[data-test='captcha']",
)


def detect_captcha(page: Any) -> tuple[bool, str]:
    """Return (detected, reason). Never attempts bypass."""
    try:
        url = (page.url or "").lower()
        if "checkpoint" in url or "captcha" in url:
            return True, "Security checkpoint URL detected"
    except Exception:
        pass

    for selector in CAPTCHA_SELECTORS:
        try:
            if page.locator(selector).count() > 0:
                return True, f"CAPTCHA element detected ({selector})"
        except Exception:
            continue

    try:
        body = (page.locator("body").inner_text(timeout=4000) or "").lower()
        for hint in CAPTCHA_HINTS:
            if hint in body:
                return True, f"CAPTCHA hint in page: {hint}"
    except Exception:
        pass

    return False, ""
