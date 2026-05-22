"""Celery application configuration placeholder."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "career_os",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Future: autodiscover_tasks from app.workers, app.automation, etc.
# celery_app.autodiscover_tasks(["app.workers"])
