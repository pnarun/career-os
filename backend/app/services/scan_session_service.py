import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.models.scan_session import ScanSessionDocument, ScanSummaryDetail

logger = logging.getLogger(__name__)

SCAN_SESSIONS_COLLECTION = "scan_sessions"


class ScanSessionServiceError(Exception):
    """Raised when scan session persistence fails."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_collection() -> AsyncIOMotorCollection:
    return get_database()[SCAN_SESSIONS_COLLECTION]


async def ensure_scan_session_indexes() -> None:
    from app.db.indexes import ensure_collection_indexes

    await ensure_collection_indexes(SCAN_SESSIONS_COLLECTION)


async def save_scan_session(
    scan_id: str,
    scan_timestamp: str,
    summary: ScanSummaryDetail,
    resume_id: str = "",
    *,
    user_id: str = "",
    workspace_id: str = "",
) -> ScanSessionDocument:
    """Persist scan analytics for historical summaries."""
    document: dict[str, Any] = {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "scan_id": scan_id,
        "scan_timestamp": scan_timestamp,
        "total_fetched": summary.total_fetched,
        "qualified_jobs": summary.qualified_jobs,
        "rejected_jobs": summary.rejected_jobs,
        "duplicates_removed": summary.duplicates_removed,
        "source_breakdown": summary.sources,
        "failed_sources": summary.failed_sources,
        "location_breakdown": summary.locations,
        "top_source": summary.top_source,
        "top_source_count": summary.top_source_count,
        "resume_id": resume_id,
        "provider_status": summary.provider_status,
        "source_errors": summary.source_errors,
        "created_at": _utc_now_iso(),
    }

    try:
        collection = _get_collection()
        result = await collection.insert_one(document)
        document["_id"] = result.inserted_id
        logger.info("Scan session analytics saved: scan_id=%s", scan_id)
        return ScanSessionDocument.from_mongo(document)
    except RuntimeError as exc:
        raise ScanSessionServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to save scan session analytics")
        raise ScanSessionServiceError("Failed to save scan session") from exc


async def get_latest_scan_session(user_id: str) -> ScanSessionDocument | None:
    """Return most recent scan session analytics for a user."""
    try:
        collection = _get_collection()
        document = await collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)],
        )
        if not document:
            return None
        return ScanSessionDocument.from_mongo(document)
    except RuntimeError as exc:
        raise ScanSessionServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to fetch latest scan session")
        raise ScanSessionServiceError("Failed to fetch scan session") from exc


async def get_scan_session_by_scan_id(
    scan_id: str,
    *,
    user_id: str | None = None,
) -> ScanSessionDocument | None:
    try:
        collection = _get_collection()
        query: dict[str, Any] = {"scan_id": scan_id}
        if user_id:
            query["user_id"] = user_id
        document = await collection.find_one(query)
        if not document:
            return None
        return ScanSessionDocument.from_mongo(document)
    except RuntimeError as exc:
        raise ScanSessionServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to fetch scan session scan_id=%s", scan_id)
        raise ScanSessionServiceError("Failed to fetch scan session") from exc


async def list_recent_scan_sessions(
    user_id: str,
    limit: int = 10,
) -> list[ScanSessionDocument]:
    """Historical scan summaries (newest first) for a user."""
    try:
        collection = _get_collection()
        effective_limit = min(max(1, limit), 50)
        cursor = (
            collection.find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(effective_limit)
        )
        documents = await cursor.to_list(length=effective_limit)
        return [ScanSessionDocument.from_mongo(doc) for doc in documents]
    except RuntimeError as exc:
        raise ScanSessionServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to list scan sessions")
        raise ScanSessionServiceError("Failed to list scan sessions") from exc
