"""Persist copilot chat history and recurring insight memory."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database

logger = logging.getLogger(__name__)

INSIGHTS_COLLECTION = "copilot_insights"
SESSIONS_COLLECTION = "copilot_sessions"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _insights_col() -> AsyncIOMotorCollection:
    return get_database()[INSIGHTS_COLLECTION]


def _sessions_col() -> AsyncIOMotorCollection:
    return get_database()[SESSIONS_COLLECTION]


async def ensure_copilot_indexes() -> None:
    insights = _insights_col()
    sessions = _sessions_col()
    await insights.create_index([("created_at", -1)])
    await insights.create_index("session_id")
    await insights.create_index("insight_type")
    await sessions.create_index("session_id", unique=True)
    await sessions.create_index([("updated_at", -1)])
    logger.info("Copilot insight indexes ensured")


async def save_chat_turn(
    *,
    session_id: str,
    user_message: str,
    assistant_message: str,
    intent: str,
    recommendations: list[dict[str, Any]] | None = None,
    reasons: list[str] | None = None,
) -> None:
    now = _utc_now_iso()
    col = _insights_col()
    await col.insert_one({
        "session_id": session_id,
        "insight_type": "chat_turn",
        "intent": intent,
        "user_message": user_message,
        "assistant_message": assistant_message,
        "recommendations": recommendations or [],
        "reasons": reasons or [],
        "created_at": now,
    })
    await _sessions_col().update_one(
        {"session_id": session_id},
        {
            "$set": {"session_id": session_id, "updated_at": now},
            "$push": {
                "messages": {
                    "$each": [
                        {"role": "user", "content": user_message, "at": now},
                        {"role": "assistant", "content": assistant_message, "at": now},
                    ],
                    "$slice": -40,
                }
            },
        },
        upsert=True,
    )


async def record_insight(
    *,
    insight_type: str,
    title: str,
    message: str,
    metadata: dict[str, Any] | None = None,
    session_id: str = "",
) -> None:
    await _insights_col().insert_one({
        "session_id": session_id,
        "insight_type": insight_type,
        "title": title,
        "message": message,
        "metadata": metadata or {},
        "created_at": _utc_now_iso(),
    })


async def list_insight_history(limit: int = 30) -> list[dict[str, Any]]:
    cursor = _insights_col().find({}).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["id"] = str(doc.pop("_id", ""))
    return docs


async def get_recurring_themes(limit: int = 10) -> dict[str, Any]:
    """Summarize recurring weaknesses and strengths from stored insights."""
    cursor = _insights_col().find({"insight_type": {"$in": ["chat_turn", "recommendation"]}}).sort("created_at", -1).limit(50)
    docs = await cursor.to_list(length=50)

    intents: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    for doc in docs:
        intent = doc.get("intent", "")
        if intent:
            intents[intent] = intents.get(intent, 0) + 1
        for reason in doc.get("reasons") or []:
            key = reason[:80]
            reason_counts[key] = reason_counts.get(key, 0) + 1

    top_intents = sorted(intents.items(), key=lambda x: -x[1])[:5]
    recurring = sorted(reason_counts.items(), key=lambda x: -x[1])[:5]

    return {
        "frequent_topics": [{"topic": t, "count": c} for t, c in top_intents],
        "recurring_recommendations": [{"reason": r, "count": c} for r, c in recurring],
    }
