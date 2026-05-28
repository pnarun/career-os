"""Cache invalidation hooks for user-scoped response caches."""

from __future__ import annotations

import logging

from app.services.cache_service import invalidate_user_caches

logger = logging.getLogger(__name__)


def invalidate_after_scan_complete(user_id: str) -> None:
    if not user_id:
        return
    invalidate_user_caches(user_id)
    logger.info(
        "Invalidated user caches after scan user_id=%s",
        user_id,
        extra={"event": "cache_invalidate_scan", "user_id": user_id},
    )


def invalidate_after_jobs_mutated(user_id: str) -> None:
    if not user_id:
        return
    invalidate_user_caches(user_id)
    logger.info(
        "Invalidated user caches after jobs update user_id=%s",
        user_id,
        extra={"event": "cache_invalidate_jobs", "user_id": user_id},
    )


def invalidate_after_analytics_refresh(user_id: str) -> None:
    if not user_id:
        return
    invalidate_user_caches(user_id)
    logger.info(
        "Invalidated user caches after analytics refresh user_id=%s",
        user_id,
        extra={"event": "cache_invalidate_analytics", "user_id": user_id},
    )
