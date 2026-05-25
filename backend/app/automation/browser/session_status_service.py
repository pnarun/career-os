"""
Session file validation and metadata tracking for Playwright storage states.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.automation.browser.session_manager import (
    PROFILES_DIR,
    SUPPORTED_PLATFORMS,
    normalize_platform,
    session_exists,
    _session_path,
)
from app.core.user_context import get_request_user_id

logger = logging.getLogger(__name__)

METADATA_PATH = PROFILES_DIR / "session_metadata.json"
SessionStatus = Literal["none", "ready", "corrupted"]

_EMPTY_ENTRY: dict[str, Any] = {
    "exists": False,
    "last_saved_at": None,
    "cookie_count": 0,
    "storage_size_kb": 0,
    "status": "none",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_metadata_file() -> dict[str, Any]:
    if not METADATA_PATH.is_file():
        return {}
    try:
        return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("[AUTOMATION][SESSION_META] read failed: %s", exc)
        return {}


def _write_metadata_file(data: dict[str, Any]) -> None:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _count_cookies(storage: dict[str, Any]) -> int:
    cookies = storage.get("cookies")
    if isinstance(cookies, list):
        return len(cookies)
    return 0


def _has_storage_content(storage: dict[str, Any]) -> bool:
    cookies = storage.get("cookies")
    origins = storage.get("origins")
    if isinstance(cookies, list) and len(cookies) > 0:
        return True
    if isinstance(origins, list) and len(origins) > 0:
        return True
    return False


def validate_session_file(platform: str, user_id: str | None = None) -> dict[str, Any]:
    """
    Validate session JSON on disk.

    Returns dict with status (none|ready|corrupted), cookie_count, storage_size_kb.
    """
    key = normalize_platform(platform)
    uid = user_id or get_request_user_id()
    path = _session_path(key, uid)

    if not path.is_file() or path.stat().st_size == 0:
        return {
            "status": "none",
            "cookie_count": 0,
            "storage_size_kb": 0,
            "exists": False,
        }

    size_kb = round(path.stat().st_size / 1024, 1)

    try:
        storage = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "[AUTOMATION][SESSION_META] corrupt json platform=%s error=%s",
            key,
            exc,
        )
        return {
            "status": "corrupted",
            "cookie_count": 0,
            "storage_size_kb": size_kb,
            "exists": True,
        }

    if not isinstance(storage, dict) or not _has_storage_content(storage):
        return {
            "status": "corrupted",
            "cookie_count": _count_cookies(storage) if isinstance(storage, dict) else 0,
            "storage_size_kb": size_kb,
            "exists": True,
        }

    return {
        "status": "ready",
        "cookie_count": _count_cookies(storage),
        "storage_size_kb": size_kb,
        "exists": True,
    }


def get_session_metadata(platform: str) -> dict[str, Any]:
    """Return merged metadata + validation for one platform."""
    key = normalize_platform(platform)
    stored = _read_metadata_file().get(key, {})
    validation = validate_session_file(key)

    status: SessionStatus = validation["status"]
    if validation["status"] == "ready" and stored.get("last_saved_at"):
        pass
    elif validation["status"] == "none":
        status = "none"

    return {
        "exists": validation["exists"],
        "last_saved_at": stored.get("last_saved_at"),
        "cookie_count": validation["cookie_count"],
        "storage_size_kb": validation["storage_size_kb"],
        "status": status,
    }


def refresh_session_metadata(platform: str) -> dict[str, Any]:
    """Re-scan session file and persist metadata entry."""
    key = normalize_platform(platform)
    validation = validate_session_file(key)
    meta = _read_metadata_file()

    entry: dict[str, Any] = {
        "exists": validation["exists"],
        "cookie_count": validation["cookie_count"],
        "storage_size_kb": validation["storage_size_kb"],
        "status": validation["status"],
        "last_saved_at": meta.get(key, {}).get("last_saved_at"),
    }

    if validation["status"] == "ready":
        entry["last_saved_at"] = _utc_now_iso()
        entry["exists"] = True
    elif validation["status"] == "none":
        entry = dict(_EMPTY_ENTRY)

    meta[key] = entry
    _write_metadata_file(meta)
    logger.info(
        "[AUTOMATION][SESSION_META] refreshed platform=%s status=%s cookies=%d",
        key,
        entry["status"],
        entry["cookie_count"],
    )
    return get_session_metadata(key)


def delete_session(platform: str, user_id: str | None = None) -> dict[str, Any]:
    """Remove session file and clear metadata."""
    key = normalize_platform(platform)
    uid = user_id or get_request_user_id()
    path = _session_path(key, uid)

    if path.is_file():
        try:
            path.unlink()
            logger.info("[AUTOMATION][SESSION_META] deleted file platform=%s", key)
        except OSError as exc:
            logger.exception("[AUTOMATION][SESSION_META] delete failed platform=%s", key)
            raise RuntimeError(f"Could not delete session file: {exc}") from exc

    meta = _read_metadata_file()
    meta[key] = dict(_EMPTY_ENTRY)
    _write_metadata_file(meta)

    return get_session_metadata(key)


def get_all_sessions_status() -> dict[str, dict[str, Any]]:
    """Status for every supported platform (API shape)."""
    result: dict[str, dict[str, Any]] = {}
    meta = _read_metadata_file()

    for platform in sorted(SUPPORTED_PLATFORMS):
        validation = validate_session_file(platform)
        stored = meta.get(platform, {})

        status: SessionStatus = validation["status"]
        last_saved = stored.get("last_saved_at")

        if validation["status"] == "ready":
            if not last_saved:
                path = _session_path(platform, uid)
                if path.is_file():
                    mtime = datetime.fromtimestamp(
                        path.stat().st_mtime,
                        tz=timezone.utc,
                    )
                    last_saved = mtime.isoformat()
        elif validation["status"] in ("none", "corrupted"):
            if validation["status"] == "none":
                last_saved = None

        result[platform] = {
            "status": status,
            "last_saved_at": last_saved,
            "cookie_count": validation["cookie_count"],
            "storage_size_kb": validation["storage_size_kb"],
            "exists": validation["exists"],
        }

    return result


def is_session_ready(platform: str, user_id: str | None = None) -> bool:
    return validate_session_file(platform, user_id)["status"] == "ready"
