"""BSON Date helpers for MongoDB TTL indexes (TTL requires Date, not ISO strings)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now_dt() -> datetime:
    return datetime.now(timezone.utc)


def coerce_to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None
    return None


def ttl_created_at(value: Any = None) -> datetime:
    """Value for ``created_at`` on insert (TTL + API-safe reads via coerce_to_iso)."""
    return coerce_to_datetime(value) or utc_now_dt()


def ttl_updated_at(value: Any = None) -> datetime:
    """Value for ``updated_at`` on upsert/update."""
    return coerce_to_datetime(value) or utc_now_dt()


def coerce_to_iso(value: Any) -> str:
    """Normalize Mongo Date or ISO string for API models."""
    dt = coerce_to_datetime(value)
    if dt is not None:
        return dt.isoformat()
    return str(value) if value is not None else ""
