"""Background scan tasks."""

from __future__ import annotations

import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.logging_config import log_event
from app.core.metrics import metrics
from app.services.scan_runner_service import ScanRunnerError, run_scan_for_user, run_scan_now
from app.services.user_preferences_service import get_preferences_by_id

logger = logging.getLogger(__name__)


def _run_async(coro):
    return asyncio.run(coro)


@celery_app.task(
    bind=True,
    name="queues.scan_tasks.run_manual_scan",
    max_retries=2,
    default_retry_delay=30,
    queue="scans",
)
def run_manual_scan_task(self, preference_id: str, user_id: str) -> dict:
    """Execute a manual scan off the API hot path."""
    log_event(
        logger,
        logging.INFO,
        "scan_task_started",
        f"Manual scan queued preference_id={preference_id}",
        task_id=self.request.id,
        queue="scans",
    )
    metrics.incr("queue_scan_started")
    try:
        preferences = _run_async(get_preferences_by_id(preference_id, user_id=user_id))
        result = _run_async(run_scan_now(preferences))
        metrics.incr("queue_scan_completed")
        return {
            "status": "success",
            "scan_id": result.scan_id,
            "stored": result.stored,
            "emailed": result.emailed,
        }
    except ScanRunnerError as exc:
        metrics.incr("queue_scan_failed")
        log_event(
            logger,
            logging.ERROR,
            "scan_task_failed",
            str(exc),
            task_id=self.request.id,
            status="failed",
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    bind=True,
    name="queues.scan_tasks.run_scheduled_scan",
    max_retries=2,
    default_retry_delay=60,
    queue="scans",
)
def run_scheduled_scan_task(self, preference_id: str) -> dict:
    """Execute a scheduled scan via worker."""
    metrics.incr("queue_scheduled_scan_started")
    try:
        preferences = _run_async(get_preferences_by_id(preference_id))
        result = _run_async(run_scan_for_user(preferences))
        metrics.incr("queue_scheduled_scan_completed")
        return {
            "status": "success",
            "scan_id": result.scan_id,
            "stored": result.stored,
            "emailed": result.emailed,
        }
    except ScanRunnerError as exc:
        metrics.incr("queue_scheduled_scan_failed")
        raise self.retry(exc=exc) from exc
