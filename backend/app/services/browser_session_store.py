"""Per-user Playwright storage_state in MongoDB (production-safe, survives redeploys)."""

from __future__ import annotations

import json
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Literal

from app.automation.browser.session_manager import (
    SUPPORTED_PLATFORMS,
    normalize_platform,
    _session_path,
)
from app.core.database import DATABASE_NAME, get_database

logger = logging.getLogger(__name__)

COLLECTION = "browser_sessions"
SessionStatus = Literal["none", "ready", "corrupted"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_cookies(storage: dict[str, Any]) -> int:
    cookies = storage.get("cookies")
    return len(cookies) if isinstance(cookies, list) else 0


def _has_storage_content(storage: dict[str, Any]) -> bool:
    cookies = storage.get("cookies")
    origins = storage.get("origins")
    if isinstance(cookies, list) and cookies:
        return True
    if isinstance(origins, list) and origins:
        return True
    return False


def _cookie_list(storage: dict[str, Any]) -> list[dict[str, Any]]:
    cookies = storage.get("cookies")
    return cookies if isinstance(cookies, list) else []


def _has_li_at_cookie(storage: dict[str, Any]) -> bool:
    for cookie in _cookie_list(storage):
        if (cookie.get("name") or "").lower() == "li_at" and (cookie.get("value") or "").strip():
            return True
    return False


def _validate_storage_dict(storage: Any, *, platform: str | None = None) -> SessionStatus:
    if not isinstance(storage, dict) or not _has_storage_content(storage):
        return "corrupted"
    if platform == "linkedin" and not _has_li_at_cookie(storage):
        return "corrupted"
    return "ready"


def _size_kb(storage: dict[str, Any]) -> float:
    try:
        return round(len(json.dumps(storage, ensure_ascii=False).encode("utf-8")) / 1024, 1)
    except (TypeError, ValueError):
        return 0.0


def _sync_client():
    from pymongo import MongoClient

    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        raise RuntimeError("MONGO_URI is not set")
    return MongoClient(uri, serverSelectionTimeoutMS=8000)


def _load_file_storage(platform: str, user_id: str | None) -> dict[str, Any] | None:
    path = _session_path(platform, user_id)
    if not path.is_file() or path.stat().st_size == 0:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def _write_file_storage(platform: str, user_id: str, storage: dict[str, Any]) -> None:
    path = _session_path(platform, user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(storage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def ensure_browser_session_indexes() -> None:
    col = get_database()[COLLECTION]
    await col.create_index([("user_id", 1), ("platform", 1)], unique=True)
    await col.create_index("updated_at")
    await col.create_index(
        [("extension_sync_token", 1)],
        unique=True,
        sparse=True,
    )


async def save_storage_state(
    *,
    user_id: str,
    platform: str,
    storage_state: dict[str, Any],
    user_agent: str = "",
    session_source: str = "",
) -> dict[str, Any]:
    key = normalize_platform(platform)
    uid = user_id.strip()
    if not uid:
        raise ValueError("user_id is required")

    status = _validate_storage_dict(storage_state, platform=key)
    if status != "ready":
        raise ValueError("Invalid storage_state: missing cookies or local storage data")

    existing = await get_database()[COLLECTION].find_one(
        {"user_id": uid, "platform": key},
        projection={"extension_sync_token": 1},
    )
    sync_token = (existing or {}).get("extension_sync_token") or secrets.token_urlsafe(32)

    doc = {
        "user_id": uid,
        "platform": key,
        "storage_state": storage_state,
        "updated_at": _utc_now_iso(),
        "cookie_count": _count_cookies(storage_state),
        "storage_size_kb": _size_kb(storage_state),
        "status": status,
        "has_li_at": _has_li_at_cookie(storage_state),
        "user_agent": (user_agent or "").strip(),
        "session_source": (session_source or "").strip(),
        "extension_sync_token": sync_token,
    }
    await get_database()[COLLECTION].replace_one(
        {"user_id": uid, "platform": key},
        doc,
        upsert=True,
    )
    doc["extension_sync_token"] = sync_token
    _write_file_storage(key, uid, storage_state)
    logger.info("[SESSION_STORE] saved user=%s platform=%s", uid, key)
    return doc


async def find_user_id_by_extension_sync_token(sync_token: str) -> str | None:
    token = (sync_token or "").strip()
    if not token:
        return None
    doc = await get_database()[COLLECTION].find_one(
        {"extension_sync_token": token, "platform": "linkedin"},
        projection={"user_id": 1},
    )
    if not doc:
        return None
    return str(doc.get("user_id") or "").strip() or None


async def delete_storage_state(*, user_id: str, platform: str) -> None:
    key = normalize_platform(platform)
    uid = user_id.strip()
    await get_database()[COLLECTION].delete_one({"user_id": uid, "platform": key})
    path = _session_path(key, uid)
    if path.is_file():
        path.unlink(missing_ok=True)
    logger.info("[SESSION_STORE] deleted user=%s platform=%s", uid, key)


async def load_storage_state(
    *,
    user_id: str | None,
    platform: str,
) -> dict[str, Any] | None:
    key = normalize_platform(platform)
    uid = (user_id or "").strip()
    if uid:
        doc = await get_database()[COLLECTION].find_one(
            {"user_id": uid, "platform": key},
            projection={"storage_state": 1},
        )
        if doc and isinstance(doc.get("storage_state"), dict):
            return doc["storage_state"]
    return _load_file_storage(key, uid or None)


def load_storage_state_sync(
    *,
    user_id: str | None,
    platform: str,
) -> dict[str, Any] | None:
    """Worker subprocess — sync Mongo read with filesystem fallback."""
    bundle = load_session_bundle_sync(user_id=user_id, platform=platform)
    return bundle.get("storage_state") if bundle else None


def load_session_bundle_sync(
    *,
    user_id: str | None,
    platform: str,
) -> dict[str, Any] | None:
    """Storage state plus Playwright context hints (user agent, li_at flag)."""
    key = normalize_platform(platform)
    uid = (user_id or "").strip()
    if uid:
        try:
            with _sync_client() as client:
                doc = client[DATABASE_NAME][COLLECTION].find_one(
                    {"user_id": uid, "platform": key},
                    projection={"storage_state": 1, "user_agent": 1, "has_li_at": 1},
                )
            if doc and isinstance(doc.get("storage_state"), dict):
                storage = doc["storage_state"]
                return {
                    "storage_state": storage,
                    "user_agent": str(doc.get("user_agent") or "").strip(),
                    "has_li_at": bool(doc.get("has_li_at"))
                    or _has_li_at_cookie(storage),
                }
        except Exception as exc:
            logger.warning("[SESSION_STORE] sync bundle load failed: %s", exc)

    file_storage = _load_file_storage(key, uid or None)
    if file_storage is None:
        return None
    return {
        "storage_state": file_storage,
        "user_agent": "",
        "has_li_at": _has_li_at_cookie(file_storage),
    }


async def get_session_info(*, user_id: str, platform: str) -> dict[str, Any]:
    key = normalize_platform(platform)
    uid = user_id.strip()
    doc = await get_database()[COLLECTION].find_one({"user_id": uid, "platform": key})
    if doc:
        status: SessionStatus = doc.get("status") or _validate_storage_dict(
            doc.get("storage_state"),
            platform=key,
        )
        return {
            "status": status,
            "last_saved_at": doc.get("updated_at"),
            "cookie_count": int(doc.get("cookie_count") or 0),
            "storage_size_kb": float(doc.get("storage_size_kb") or 0),
            "exists": status == "ready",
        }

    file_storage = _load_file_storage(key, uid)
    if file_storage is None:
        return {
            "status": "none",
            "last_saved_at": None,
            "cookie_count": 0,
            "storage_size_kb": 0.0,
            "exists": False,
        }

    status = _validate_storage_dict(file_storage, platform=key)
    path = _session_path(key, uid)
    mtime = None
    if path.is_file():
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    return {
        "status": status,
        "last_saved_at": mtime,
        "cookie_count": _count_cookies(file_storage),
        "storage_size_kb": round(path.stat().st_size / 1024, 1) if path.is_file() else _size_kb(file_storage),
        "exists": status == "ready",
    }


def get_all_session_info_sync(*, user_id: str) -> dict[str, dict[str, Any]]:
    uid = user_id.strip()
    result: dict[str, dict[str, Any]] = {}
    for platform in sorted(SUPPORTED_PLATFORMS):
        result[platform] = _get_session_info_sync(user_id=uid, platform=platform)
    return result


def _get_session_info_sync(*, user_id: str, platform: str) -> dict[str, Any]:
    key = normalize_platform(platform)
    uid = user_id.strip()
    try:
        with _sync_client() as client:
            doc = client[DATABASE_NAME][COLLECTION].find_one(
                {"user_id": uid, "platform": key}
            )
        if doc:
            status: SessionStatus = doc.get("status") or _validate_storage_dict(
                doc.get("storage_state"),
                platform=key,
            )
            return {
                "status": status,
                "last_saved_at": doc.get("updated_at"),
                "cookie_count": int(doc.get("cookie_count") or 0),
                "storage_size_kb": float(doc.get("storage_size_kb") or 0),
                "exists": status == "ready",
            }
    except Exception as exc:
        logger.warning("[SESSION_STORE] info sync failed: %s", exc)

    file_storage = _load_file_storage(key, uid)
    if file_storage is None:
        return {
            "status": "none",
            "last_saved_at": None,
            "cookie_count": 0,
            "storage_size_kb": 0.0,
            "exists": False,
        }
    status = _validate_storage_dict(file_storage, platform=key)
    path = _session_path(key, uid)
    mtime = None
    if path.is_file():
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    return {
        "status": status,
        "last_saved_at": mtime,
        "cookie_count": _count_cookies(file_storage),
        "storage_size_kb": round(path.stat().st_size / 1024, 1) if path.is_file() else _size_kb(file_storage),
        "exists": status == "ready",
    }


def is_storage_ready(*, user_id: str | None, platform: str) -> bool:
    bundle = load_session_bundle_sync(user_id=user_id, platform=platform)
    if not bundle:
        return False
    storage = bundle.get("storage_state")
    if not isinstance(storage, dict):
        return False
    key = normalize_platform(platform)
    if key == "linkedin" and not bundle.get("has_li_at"):
        return False
    return _validate_storage_dict(storage, platform=key) == "ready"


def save_storage_state_sync(
    *,
    user_id: str,
    platform: str,
    storage_state: dict[str, Any],
) -> None:
    key = normalize_platform(platform)
    uid = user_id.strip()
    status = _validate_storage_dict(storage_state, platform=key)
    if status != "ready":
        raise ValueError("Invalid storage_state")

    doc = {
        "user_id": uid,
        "platform": key,
        "storage_state": storage_state,
        "updated_at": _utc_now_iso(),
        "cookie_count": _count_cookies(storage_state),
        "storage_size_kb": _size_kb(storage_state),
        "status": status,
        "has_li_at": _has_li_at_cookie(storage_state),
    }
    with _sync_client() as client:
        client[DATABASE_NAME][COLLECTION].replace_one(
            {"user_id": uid, "platform": key},
            doc,
            upsert=True,
        )
    _write_file_storage(key, uid, storage_state)
