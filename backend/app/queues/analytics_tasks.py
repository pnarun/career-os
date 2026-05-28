"""Background analytics generation tasks."""

from __future__ import annotations

import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.cache import cache_delete, cache_key
from app.core.metrics import metrics
from app.services.cache_invalidation import invalidate_after_analytics_refresh

logger = logging.getLogger(__name__)


def _run_async(coro):
    return asyncio.run(coro)


@celery_app.task(name="queues.analytics_tasks.refresh_career_insights", queue="analytics")
def refresh_career_insights_task(user_id: str) -> dict:
    """Invalidate cached analytics and trigger regeneration hook."""
    metrics.incr("queue_analytics_started")
    cache_delete(cache_key("analytics", user_id))
    cache_delete(cache_key("copilot", "recommendations", user_id))
    invalidate_after_analytics_refresh(user_id)
    logger.info(
        "Analytics cache invalidated user_id=%s",
        user_id,
        extra={"event": "analytics_refresh", "status": "success"},
    )
    metrics.incr("queue_analytics_completed")
    return {"status": "invalidated", "user_id": user_id}
