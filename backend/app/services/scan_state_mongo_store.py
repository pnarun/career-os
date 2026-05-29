"""MongoDB persistence for distributed scan progress (API + scan worker)."""

from __future__ import annotations

import logging
import os
from typing import Any

from app.models.scan_state import ScanState

logger = logging.getLogger(__name__)

COLLECTION = "scan_states"


def _sync_collection():
    from pymongo import MongoClient

    uri = (os.getenv("MONGO_URI") or "").strip()
    if not uri:
        return None
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    return client.get_database("career_os")[COLLECTION]


def save_scan_state(state: ScanState) -> bool:
    """Upsert scan state to MongoDB. Returns False if Mongo is unavailable."""
    col = _sync_collection()
    if col is None:
        return False
    try:
        doc: dict[str, Any] = state.model_dump(mode="json")
        doc["scan_id"] = state.scan_id
        col.replace_one({"scan_id": state.scan_id}, doc, upsert=True)
        logger.info(
            "[SCAN_PROGRESS_WRITE] scan_id=%s status=%s progress=%s",
            state.scan_id,
            state.status,
            state.progress,
            extra={
                "event": "SCAN_PROGRESS_WRITE",
                "scan_id": state.scan_id,
                "status": state.status,
                "progress": state.progress,
            },
        )
        return True
    except Exception as exc:
        logger.warning(
            "scan_states mongo save failed scan_id=%s: %s",
            state.scan_id,
            exc,
            extra={"event": "scan_state_mongo_save_failed", "scan_id": state.scan_id},
        )
        return False


def load_scan_state(scan_id: str) -> ScanState | None:
    """Load scan state from MongoDB."""
    col = _sync_collection()
    if col is None:
        return None
    try:
        doc = col.find_one({"scan_id": scan_id})
        if not doc:
            return None
        payload = dict(doc)
        payload.pop("_id", None)
        return ScanState.model_validate(payload)
    except Exception as exc:
        logger.debug("scan_states mongo load failed scan_id=%s: %s", scan_id, exc)
        return None


def delete_scan_state(scan_id: str) -> None:
    col = _sync_collection()
    if col is None:
        return
    try:
        col.delete_one({"scan_id": scan_id})
    except Exception as exc:
        logger.debug("scan_states mongo delete failed scan_id=%s: %s", scan_id, exc)
