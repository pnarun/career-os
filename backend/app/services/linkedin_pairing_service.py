from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import ReturnDocument

from app.core.database import get_database

COLLECTION = "linkedin_pairing_sessions"
PAIRING_TTL_SECONDS = 300


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _normalize_code(raw: str) -> str:
    code = "".join(ch for ch in str(raw or "") if ch.isdigit())
    if len(code) != 6:
        raise ValueError("Pairing code must be a 6-digit number.")
    return code


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def ensure_linkedin_pairing_indexes() -> None:
    col = get_database()[COLLECTION]
    await col.create_index("pairing_code")
    await col.create_index([("user_id", 1), ("used", 1), ("expires_at", 1)])
    await col.create_index("created_at")
    await col.create_index("expires_at")


async def create_pairing_code(*, user_id: str) -> dict[str, Any]:
    uid = (user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    col = get_database()[COLLECTION]
    now = _utc_now()
    expires_at = now + timedelta(seconds=PAIRING_TTL_SECONDS)

    # One active pairing per user: invalidate older active rows.
    await col.update_many(
        {"user_id": uid, "used": False, "expires_at": {"$gt": now}},
        {"$set": {"used": True, "used_at": now}},
    )

    code = ""
    for _ in range(10):
        candidate = _generate_code()
        exists = await col.find_one(
            {
                "pairing_code": candidate,
                "used": False,
                "expires_at": {"$gt": now},
            },
            projection={"_id": 1},
        )
        if not exists:
            code = candidate
            break
    if not code:
        raise RuntimeError("Unable to generate pairing code. Please retry.")

    await col.insert_one(
        {
            "pairing_code": code,
            "user_id": uid,
            "created_at": now,
            "expires_at": expires_at,
            "used": False,
            "used_at": None,
            "extension_version": "",
        }
    )
    return {
        "pairing_code": code,
        "expires_in": PAIRING_TTL_SECONDS,
        "expires_at": _to_iso(expires_at),
    }


async def redeem_pairing_code(
    *,
    pairing_code: str,
    extension_version: str = "",
) -> dict[str, Any]:
    code = _normalize_code(pairing_code)
    now = _utc_now()
    col = get_database()[COLLECTION]

    doc = await col.find_one_and_update(
        {
            "pairing_code": code,
            "used": False,
            "expires_at": {"$gt": now},
        },
        {
            "$set": {
                "used": True,
                "used_at": now,
                "extension_version": (extension_version or "").strip(),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if doc:
        return {"user_id": str(doc.get("user_id") or ""), "used_at": _to_iso(now)}

    existing = await col.find_one({"pairing_code": code}, sort=[("created_at", -1)])
    if not existing:
        raise ValueError("Invalid pairing code.")
    if existing.get("used"):
        raise ValueError("Pairing code already used.")
    if existing.get("expires_at") and existing["expires_at"] <= now:
        raise ValueError("Pairing code expired. Generate a new code.")
    raise ValueError("Pairing code is not valid anymore. Generate a new code.")


async def invalidate_pairing_sessions_for_user(*, user_id: str) -> None:
    uid = (user_id or "").strip()
    if not uid:
        return
    now = _utc_now()
    await get_database()[COLLECTION].update_many(
        {"user_id": uid, "used": False},
        {"$set": {"used": True, "used_at": now}},
    )
