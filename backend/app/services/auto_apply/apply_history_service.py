"""Apply session and history persistence."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.models.auto_apply import (
    ApplyAnalytics,
    ApplySessionCreate,
    ApplySessionDocument,
    DetectedQuestion,
    FilledField,
)

logger = logging.getLogger(__name__)

APPLY_SESSIONS_COLLECTION = "apply_sessions"
APPLY_HISTORY_COLLECTION = "apply_history"
APPLY_ERRORS_COLLECTION = "apply_errors"

MAX_APPLIES_PER_DAY = 10
APPLY_COOLDOWN_SECONDS = 60


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_sessions_collection() -> AsyncIOMotorCollection:
    return get_database()[APPLY_SESSIONS_COLLECTION]


def _get_history_collection() -> AsyncIOMotorCollection:
    return get_database()[APPLY_HISTORY_COLLECTION]


def _get_errors_collection() -> AsyncIOMotorCollection:
    return get_database()[APPLY_ERRORS_COLLECTION]


def _sync_sessions_collection():
    """Sync MongoDB access for Playwright worker subprocess."""
    from pymongo import MongoClient

    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        raise RuntimeError("MONGO_URI not set")
    client = MongoClient(uri)
    return client["career_os"][APPLY_SESSIONS_COLLECTION]


async def ensure_apply_indexes() -> None:
    sessions = _get_sessions_collection()
    await sessions.create_index("session_id", unique=True)
    await sessions.create_index([("created_at", -1)])
    await sessions.create_index("state")

    history = _get_history_collection()
    await history.create_index([("created_at", -1)])
    await history.create_index("session_id")

    errors = _get_errors_collection()
    await errors.create_index([("created_at", -1)])
    logger.info("Auto-apply collection indexes ensured")


async def create_apply_session(payload: ApplySessionCreate) -> ApplySessionDocument:
    collection = _get_sessions_collection()
    now = _utc_now_iso()
    session_id = str(uuid.uuid4())
    document: dict[str, Any] = {
        "session_id": session_id,
        "state": "IDLE",
        "job_id": payload.job_id.strip(),
        "job_url": payload.job_url.strip(),
        "title": payload.title.strip(),
        "company": payload.company.strip(),
        "source": payload.source.strip() or "linkedin",
        "resume_id": payload.resume_id.strip(),
        "match_score": int(payload.match_score or 0),
        "filled_fields": [],
        "detected_questions": [],
        "unknown_questions": [],
        "confidence_score": 0.0,
        "screenshots": [],
        "error": "",
        "confirmation_required": False,
        "confirmed": False,
        "submitted": False,
        "application_id": "",
        "created_at": now,
        "updated_at": now,
        "metadata": {},
    }
    result = await collection.insert_one(document)
    document["_id"] = result.inserted_id
    return ApplySessionDocument.from_mongo(document)


async def get_apply_session(session_id: str) -> ApplySessionDocument | None:
    collection = _get_sessions_collection()
    document = await collection.find_one({"session_id": session_id})
    if not document:
        return None
    return ApplySessionDocument.from_mongo(document)


async def update_apply_session(session_id: str, updates: dict[str, Any]) -> ApplySessionDocument | None:
    collection = _get_sessions_collection()
    updates["updated_at"] = _utc_now_iso()
    result = await collection.find_one_and_update(
        {"session_id": session_id},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        return None
    return ApplySessionDocument.from_mongo(result)


def sync_update_apply_session(session_id: str, updates: dict[str, Any]) -> None:
    """Worker-side session update (sync pymongo)."""
    collection = _sync_sessions_collection()
    updates["updated_at"] = _utc_now_iso()
    collection.update_one({"session_id": session_id}, {"$set": updates})


async def record_apply_history(session_id: str, event: str, details: dict[str, Any] | None = None) -> None:
    collection = _get_history_collection()
    await collection.insert_one({
        "session_id": session_id,
        "event": event,
        "details": details or {},
        "created_at": _utc_now_iso(),
    })


async def record_apply_error(session_id: str, error: str, details: dict[str, Any] | None = None) -> None:
    collection = _get_errors_collection()
    await collection.insert_one({
        "session_id": session_id,
        "error": error,
        "details": details or {},
        "created_at": _utc_now_iso(),
    })
    await record_apply_history(session_id, "error", {"error": error, **(details or {})})


async def get_apply_analytics() -> ApplyAnalytics:
    collection = _get_history_collection()
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    attempts = await collection.count_documents({
        "event": "submitted",
        "created_at": {"$gte": today_start.isoformat()},
    })

    last = await collection.find_one(
        {"event": "submitted"},
        sort=[("created_at", -1)],
    )
    last_at = last.get("created_at", "") if last else ""

    can_apply = attempts < MAX_APPLIES_PER_DAY
    if last_at and can_apply:
        try:
            last_dt = datetime.fromisoformat(last_at.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
            if elapsed < APPLY_COOLDOWN_SECONDS:
                can_apply = False
        except ValueError:
            pass

    return ApplyAnalytics(
        attempts_today=attempts,
        max_per_day=MAX_APPLIES_PER_DAY,
        cooldown_seconds=APPLY_COOLDOWN_SECONDS,
        can_apply=can_apply,
        last_apply_at=last_at,
    )


def session_to_worker_payload(session: ApplySessionDocument, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "session_id": session.session_id,
        "job_url": session.job_url,
        "job_id": session.job_id,
        "title": session.title,
        "company": session.company,
        "resume_id": session.resume_id,
        "source": session.source,
    }
    if extra:
        payload.update(extra)
    return payload
