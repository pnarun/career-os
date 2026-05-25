"""Celery application — background worker engine."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "career_os",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.queues.scan_tasks",
        "app.queues.scoring_tasks",
        "app.queues.notification_tasks",
        "app.queues.analytics_tasks",
        "app.queues.retry_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_routes={
        "queues.scan_tasks.*": {"queue": "scans"},
        "queues.scoring_tasks.*": {"queue": "ai"},
        "queues.notification_tasks.*": {"queue": "email"},
        "queues.analytics_tasks.*": {"queue": "analytics"},
        "queues.retry_tasks.*": {"queue": "maintenance"},
    },
    beat_schedule={
        "flush-failed-jobs-hourly": {
            "task": "queues.retry_tasks.flush_failed_jobs",
            "schedule": crontab(minute=0),
        },
    },
)
