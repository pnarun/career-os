"""Celery worker entrypoint.

Run:
    celery -A app.core.celery_app:celery_app worker -Q scans,email,ai,analytics,maintenance,default -l info

Scheduler (beat):
    celery -A app.core.celery_app:celery_app beat -l info
"""

from app.core.celery_app import celery_app
from app.core.logging_config import configure_logging

configure_logging(service="career-os-worker")

__all__ = ["celery_app"]
