"""Retry and dead-letter maintenance tasks."""

from __future__ import annotations

import logging

from app.core.celery_app import celery_app
from app.core.metrics import metrics
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)


@celery_app.task(name="queues.retry_tasks.flush_failed_jobs", queue="maintenance")
def flush_failed_jobs_task() -> dict:
    """Report Celery failure counters from Redis backend."""
    metrics.incr("queue_maintenance_run")
    redis_client = get_redis()
    failed = 0
    if redis_client:
        try:
            failed = len(list(redis_client.scan_iter(match="celery-task-meta-*", count=100)))
        except Exception:
            pass
    logger.info(
        "Maintenance flush failed_meta=%d",
        failed,
        extra={"event": "retry_maintenance", "status": "ok"},
    )
    return {"failed_meta_keys": failed}
