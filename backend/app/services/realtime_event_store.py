"""MongoDB-backed cross-service realtime event bus (no Redis/Celery)."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.mongo_timestamps import ttl_created_at, ttl_updated_at
from app.core.retention import REALTIME_EVENT_RETENTION_DAYS

logger = logging.getLogger(__name__)

COLLECTION = "realtime_events"


def _sync_collection():
    from pymongo import MongoClient

    uri = (os.getenv("MONGO_URI") or "").strip()
    if not uri:
        return None
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    return client.get_database("career_os")[COLLECTION]


def publish_realtime_event(
    *,
    event_type: str,
    user_id: str,
    payload: dict[str, Any],
    workspace_id: str = "",
    scan_id: str = "",
) -> str | None:
    """
  Insert an unprocessed realtime event for the API bridge to fan out to WebSockets.
  Safe to call from scan-worker / automation-worker (sync pymongo).
  """
    if not user_id or not event_type:
        return None

    col = _sync_collection()
    if col is None:
        logger.debug("realtime_events publish skipped — MONGO_URI not set")
        return None

    now = ttl_created_at()
    doc = {
        "event_type": event_type,
        "workspace_id": (workspace_id or "").strip(),
        "user_id": user_id.strip(),
        "scan_id": (scan_id or "").strip(),
        "payload": payload,
        "created_at": now,
        "processed": False,
        "processed_at": None,
    }
    try:
        result = col.insert_one(doc)
        event_id = str(result.inserted_id)
        logger.info(
            "[REALTIME_EVENT] published event_id=%s type=%s user_id=%s scan_id=%s",
            event_id,
            event_type,
            user_id,
            scan_id or "-",
            extra={
                "event": "REALTIME_EVENT_PUBLISHED",
                "event_id": event_id,
                "event_type": event_type,
                "user_id": user_id,
                "scan_id": scan_id,
            },
        )
        return event_id
    except Exception as exc:
        logger.warning(
            "realtime_events publish failed type=%s user_id=%s: %s",
            event_type,
            user_id,
            exc,
            extra={"event": "REALTIME_EVENT_PUBLISH_FAILED", "event_type": event_type},
        )
        return None


def claim_unprocessed_events(*, limit: int = 32) -> list[dict[str, Any]]:
    """
    Atomically claim oldest unprocessed events (processed=True) for API delivery.
    One claim per document prevents duplicate WebSocket sends.
    """
    col = _sync_collection()
    if col is None or limit < 1:
        return []

    from pymongo import ReturnDocument

    claimed: list[dict[str, Any]] = []
    now = ttl_updated_at()
    for _ in range(limit):
        doc = col.find_one_and_update(
            {"processed": False},
            {"$set": {"processed": True, "processed_at": now}},
            sort=[("created_at", 1)],
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            break
        claimed.append(doc)
    return claimed


def mark_event_processed(event_id: str) -> None:
    """Idempotent mark (events are usually claimed atomically)."""
    col = _sync_collection()
    if col is None:
        return
    try:
        from bson import ObjectId
        from bson.errors import InvalidId

        oid = ObjectId(event_id)
    except (InvalidId, TypeError):
        return
    col.update_one(
        {"_id": oid},
        {"$set": {"processed": True, "processed_at": ttl_updated_at()}},
    )


def fetch_unprocessed_events(*, limit: int = 32) -> list[dict[str, Any]]:
    """Read-only peek at pending events (prefer claim_unprocessed_events on API)."""
    col = _sync_collection()
    if col is None:
        return []
    cursor = col.find({"processed": False}).sort("created_at", 1).limit(limit)
    return list(cursor)


def cleanup_old_events(*, extra_days: int = 1) -> int:
    """
    Best-effort cleanup of processed events older than retention + buffer.
    TTL index on created_at is the primary expiry mechanism.
    """
    col = _sync_collection()
    if col is None:
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(
        days=REALTIME_EVENT_RETENTION_DAYS + max(0, extra_days)
    )
    try:
        result = col.delete_many(
            {
                "processed": True,
                "created_at": {"$lt": cutoff},
            }
        )
        deleted = int(result.deleted_count)
        if deleted:
            logger.info(
                "realtime_events cleanup deleted=%s",
                deleted,
                extra={"event": "realtime_events_cleanup", "deleted": deleted},
            )
        return deleted
    except Exception as exc:
        logger.debug("realtime_events cleanup failed: %s", exc)
        return 0
