"""Interview preparation progress — MongoDB persistence."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database

logger = logging.getLogger(__name__)

PREP_PROGRESS_COLLECTION = "interview_prep_progress"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _collection() -> AsyncIOMotorCollection:
    return get_database()[PREP_PROGRESS_COLLECTION]


async def ensure_prep_indexes() -> None:
    col = _collection()
    await col.create_index([("updated_at", -1)])
    await col.create_index("job_id")
    logger.info("Interview prep progress indexes ensured")


async def get_progress(job_id: str = "") -> dict[str, Any]:
    query = {"job_id": job_id} if job_id else {"job_id": {"$exists": True}}
    doc = await _collection().find_one(query, sort=[("updated_at", -1)])
    if not doc:
        return {
            "practiced_questions": [],
            "completed_topics": [],
            "mock_sessions_completed": 0,
            "weak_areas": [],
            "history": [],
        }
    doc.pop("_id", None)
    return doc


async def record_practice(
    *,
    job_id: str = "",
    question_id: str,
    question_text: str,
    category: str,
) -> dict[str, Any]:
    col = _collection()
    now = _utc_now_iso()
    entry = {
        "question_id": question_id,
        "question": question_text[:200],
        "category": category,
        "practiced_at": now,
    }

    existing = await col.find_one({"job_id": job_id or "general"})
    if existing:
        practiced = existing.get("practiced_questions", [])
        if not any(p.get("question_id") == question_id for p in practiced):
            practiced.append(entry)
        await col.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "practiced_questions": practiced[-100:],
                    "updated_at": now,
                }
            },
        )
    else:
        await col.insert_one({
            "job_id": job_id or "general",
            "practiced_questions": [entry],
            "completed_topics": [],
            "mock_sessions_completed": 0,
            "weak_areas": [],
            "history": [],
            "created_at": now,
            "updated_at": now,
        })

    return await get_progress(job_id)


async def record_topic_complete(*, job_id: str = "", topic: str) -> dict[str, Any]:
    col = _collection()
    now = _utc_now_iso()
    existing = await col.find_one({"job_id": job_id or "general"})
    if existing:
        topics = list(set(existing.get("completed_topics", []) + [topic]))
        await col.update_one(
            {"_id": existing["_id"]},
            {"$set": {"completed_topics": topics, "updated_at": now}},
        )
    else:
        await col.insert_one({
            "job_id": job_id or "general",
            "practiced_questions": [],
            "completed_topics": [topic],
            "mock_sessions_completed": 0,
            "weak_areas": [],
            "history": [],
            "created_at": now,
            "updated_at": now,
        })
    return await get_progress(job_id)


async def record_mock_complete(*, job_id: str = "", session_id: str, category: str) -> dict[str, Any]:
    col = _collection()
    now = _utc_now_iso()
    existing = await col.find_one({"job_id": job_id or "general"})
    history_entry = {"session_id": session_id, "category": category, "completed_at": now}

    if existing:
        history = existing.get("history", []) + [history_entry]
        count = existing.get("mock_sessions_completed", 0) + 1
        await col.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "mock_sessions_completed": count,
                    "history": history[-50:],
                    "updated_at": now,
                }
            },
        )
    else:
        await col.insert_one({
            "job_id": job_id or "general",
            "practiced_questions": [],
            "completed_topics": [],
            "mock_sessions_completed": 1,
            "weak_areas": [],
            "history": [history_entry],
            "created_at": now,
            "updated_at": now,
        })
    return await get_progress(job_id)
