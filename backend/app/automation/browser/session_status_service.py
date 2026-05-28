"""Session file validation and metadata tracking for Playwright storage states."""

from __future__ import annotations

import logging
from typing import Any, Literal

from app.automation.browser.session_manager import SUPPORTED_PLATFORMS, normalize_platform
from app.core.user_context import get_request_user_id
from app.services.browser_session_store import (
    delete_storage_state as delete_stored_session,
    get_all_session_info_sync,
    is_storage_ready,
)

logger = logging.getLogger(__name__)

SessionStatus = Literal["none", "ready", "corrupted"]


def validate_session_file(platform: str, user_id: str | None = None) -> dict[str, Any]:
    """Validate stored session for a user + platform."""
    key = normalize_platform(platform)
    uid = user_id or get_request_user_id()
    if uid:
        info = get_all_session_info_sync(user_id=uid).get(key)
        if info:
            return {
                "status": info["status"],
                "cookie_count": info["cookie_count"],
                "storage_size_kb": info["storage_size_kb"],
                "exists": info["exists"],
            }
    return {
        "status": "none",
        "cookie_count": 0,
        "storage_size_kb": 0,
        "exists": False,
    }


def get_session_metadata(platform: str) -> dict[str, Any]:
    key = normalize_platform(platform)
    user_id = get_request_user_id()
    if not user_id:
        validation = validate_session_file(key)
        return {
            "exists": validation["exists"],
            "last_saved_at": None,
            "cookie_count": validation["cookie_count"],
            "storage_size_kb": validation["storage_size_kb"],
            "status": validation["status"],
        }
    return get_all_session_info_sync(user_id=user_id)[key]


def refresh_session_metadata(platform: str) -> dict[str, Any]:
    return get_session_metadata(platform)


async def delete_session(platform: str, user_id: str | None = None) -> dict[str, Any]:
    key = normalize_platform(platform)
    uid = user_id or get_request_user_id()
    if not uid:
        raise RuntimeError("Authenticated user required to delete session")
    await delete_stored_session(user_id=uid, platform=key)
    return get_session_metadata(key)


def get_all_sessions_status() -> dict[str, dict[str, Any]]:
    user_id = get_request_user_id()
    if user_id:
        return get_all_session_info_sync(user_id=user_id)

    result: dict[str, dict[str, Any]] = {}
    for platform in sorted(SUPPORTED_PLATFORMS):
        validation = validate_session_file(platform)
        result[platform] = {
            "status": validation["status"],
            "last_saved_at": None,
            "cookie_count": validation["cookie_count"],
            "storage_size_kb": validation["storage_size_kb"],
            "exists": validation["exists"],
        }
    return result


def is_session_ready(platform: str, user_id: str | None = None) -> bool:
    uid = user_id or get_request_user_id()
    return is_storage_ready(user_id=uid, platform=platform)

