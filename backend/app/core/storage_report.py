"""Lightweight MongoDB collection size estimates at startup."""

from __future__ import annotations

import logging

from app.core.database import get_database

logger = logging.getLogger(__name__)

MONITORED_COLLECTIONS: tuple[str, ...] = (
    "jobs",
    "scan_states",
    "scan_execution_tasks",
    "browser_sessions",
    "notifications",
)


async def log_storage_report() -> None:
    """Log estimated_document_count per monitored collection (no full scans)."""
    db = get_database()
    for name in MONITORED_COLLECTIONS:
        try:
            count = await db[name].estimated_document_count()
            logger.info(
                "[STORAGE_REPORT] collection=%s count=%s",
                name,
                count,
                extra={"event": "STORAGE_REPORT", "collection": name, "count": count},
            )
        except Exception as exc:
            logger.debug(
                "[STORAGE_REPORT] collection=%s unavailable: %s",
                name,
                exc,
                extra={"event": "STORAGE_REPORT", "collection": name, "error": str(exc)[:120]},
            )
