"""Queue task registration tests."""

import app.queues.analytics_tasks  # noqa: F401
import app.queues.notification_tasks  # noqa: F401
import app.queues.retry_tasks  # noqa: F401
import app.queues.scan_tasks  # noqa: F401
import app.queues.scoring_tasks  # noqa: F401
from app.core.celery_app import celery_app


def test_celery_tasks_registered():
    names = set(celery_app.tasks.keys())
    assert "queues.scan_tasks.run_manual_scan" in names
    assert "queues.notification_tasks.send_scan_email" in names
    assert "queues.retry_tasks.flush_failed_jobs" in names
