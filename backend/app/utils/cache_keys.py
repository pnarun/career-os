"""Standardized Redis cache key builders for Career OS."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _slug(value: str) -> str:
    cleaned = (value or "").strip().lower()
    if not cleaned:
        return "default"
    return cleaned.replace(" ", "_")[:80]


def analytics_user_key(user_id: str, *, role: str = "") -> str:
    base = f"analytics:user:{user_id}"
    if role and role.strip():
        return f"{base}:role:{_slug(role)}"
    return base


def dashboard_user_key(user_id: str) -> str:
    return f"dashboard:user:{user_id}"


def scans_latest_user_key(user_id: str) -> str:
    return f"scans:latest:{user_id}"


def scans_recent_user_key(user_id: str, *, limit: int = 10) -> str:
    return f"scans:recent:{user_id}:{int(limit)}"


def jobs_user_key(user_id: str, page: str) -> str:
    return f"jobs:user:{user_id}:{page}"


def jobs_feed_key(user_id: str, *, filters: dict[str, Any] | None = None) -> str:
    """Stable cache key for filtered jobs feed (page segment encodes filter hash)."""
    if not filters:
        return jobs_user_key(user_id, "feed")
    raw = json.dumps(filters, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return jobs_user_key(user_id, f"feed:{digest}")


def user_cache_prefixes(user_id: str) -> list[str]:
    """Prefixes used when invalidating all user-scoped response caches."""
    return [
        f"analytics:user:{user_id}",
        f"dashboard:user:{user_id}",
        f"scans:latest:{user_id}",
        f"scans:recent:{user_id}:",
        f"jobs:user:{user_id}:",
    ]
