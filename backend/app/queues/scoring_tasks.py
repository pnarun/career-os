"""Background scoring / AI workload tasks."""

from __future__ import annotations

import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.metrics import metrics

logger = logging.getLogger(__name__)


def _run_async(coro):
    return asyncio.run(coro)


@celery_app.task(name="queues.scoring_tasks.score_jobs_batch", queue="ai")
def score_jobs_batch_task(resume_id: str, job_ids: list[str]) -> dict:
    """Placeholder hook for batch scoring — delegates to existing match engine when expanded."""
    metrics.incr("queue_scoring_started")
    logger.info(
        "score_jobs_batch resume_id=%s count=%d",
        resume_id,
        len(job_ids),
        extra={"event": "scoring_task", "status": "started"},
    )
    metrics.incr("queue_scoring_completed")
    return {"status": "queued", "job_count": len(job_ids)}
