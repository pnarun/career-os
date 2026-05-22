"""Celery worker entrypoint placeholder.

Run locally (when tasks are implemented):
    celery -A app.core.celery_app:celery_app worker --loglevel=info
"""

from app.core.celery_app import celery_app

# Placeholder task registration area for future background jobs.
# @celery_app.task
# def example_task():
#     pass

__all__ = ["celery_app"]
