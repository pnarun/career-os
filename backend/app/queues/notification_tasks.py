"""Background notification and email tasks."""

from __future__ import annotations

import logging

from app.core.celery_app import celery_app
from app.core.metrics import metrics
from app.core.retry import retry_sync
from app.services.email_service import (
    EmailServiceError,
    ScanEmailSummary,
    send_scan_results_email,
)
from app.models.job import JobDocument

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="queues.notification_tasks.send_scan_email",
    max_retries=3,
    default_retry_delay=20,
    queue="email",
)
def send_scan_email_task(
    self,
    email: str,
    jobs_payload: list[dict],
    scan_id: str,
    scan_timestamp: str,
) -> dict:
    metrics.incr("queue_email_started")
    jobs = [JobDocument.model_validate(j) for j in jobs_payload]

    def _send():
        return send_scan_results_email(
            email=email,
            jobs=jobs,
            scan_summary=ScanEmailSummary(
                scan_id=scan_id,
                scan_timestamp=scan_timestamp,
            ),
        )

    try:
        delivery = retry_sync(
            _send,
            max_attempts=3,
            retry_on=(EmailServiceError,),
            label="send_scan_email",
        )
        metrics.incr("queue_email_completed")
        return {"sent": delivery.sent, "email_to": delivery.email_to}
    except EmailServiceError as exc:
        metrics.incr("queue_email_failed")
        raise self.retry(exc=exc) from exc
