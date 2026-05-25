"""
Persistent browser storage state per platform (login prep only).

No automated login — sessions are saved/loaded for future manual or guided flows.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext

logger = logging.getLogger(__name__)

AUTOMATION_ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = AUTOMATION_ROOT / "profiles"

SUPPORTED_PLATFORMS = frozenset({"linkedin", "naukri", "indeed", "instahyre"})

PLATFORM_HOME_URLS: dict[str, str] = {
    "linkedin": "https://www.linkedin.com/",
    "naukri": "https://www.naukri.com/",
    "indeed": "https://www.indeed.com/",
    "instahyre": "https://www.instahyre.com/",
}


def normalize_platform(platform: str) -> str:
    key = (platform or "").strip().lower()
    if key not in SUPPORTED_PLATFORMS:
        raise ValueError(
            f"Unsupported platform '{platform}'. "
            f"Use one of: {', '.join(sorted(SUPPORTED_PLATFORMS))}"
        )
    return key


def _session_path(platform: str, user_id: str | None = None) -> Path:
    key = normalize_platform(platform)
    if user_id:
        return PROFILES_DIR / "sessions" / user_id / f"{key}_session.json"
    return PROFILES_DIR / f"{key}_session.json"


def session_exists(platform: str, user_id: str | None = None) -> bool:
    path = _session_path(platform, user_id)
    return path.is_file() and path.stat().st_size > 0


def load_session(platform: str, user_id: str | None = None) -> dict[str, Any] | None:
    """Load Playwright storage state JSON for a platform, or None if missing."""
    path = _session_path(platform, user_id)
    if not path.is_file():
        logger.info("[AUTOMATION][SESSION] no session file platform=%s", platform)
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        logger.info("[AUTOMATION][SESSION] loaded platform=%s path=%s", platform, path)
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "[AUTOMATION][SESSION] failed to load platform=%s error=%s",
            platform,
            exc,
        )
        return None


def save_session_sync(platform: str, context: Any, user_id: str | None = None) -> Path:
    """Sync variant for thread-pool Playwright runner."""
    key = normalize_platform(platform)
    path = _session_path(key, user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(path))
    logger.info("[AUTOMATION][SESSION] saved platform=%s path=%s", key, path)
    return path


async def save_session(platform: str, context: Any, user_id: str | None = None) -> Path:
    """Persist browser storage state for a platform."""
    key = normalize_platform(platform)
    path = _session_path(key, user_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    await context.storage_state(path=str(path))
    logger.info("[AUTOMATION][SESSION] saved platform=%s path=%s", key, path)
    return path


def list_session_status() -> dict[str, dict[str, Any]]:
    """Deprecated — use session_status_service.get_all_sessions_status."""
    from app.automation.browser.session_status_service import get_all_sessions_status

    return get_all_sessions_status()


def get_platform_home_url(platform: str) -> str:
    key = normalize_platform(platform)
    return PLATFORM_HOME_URLS[key]
