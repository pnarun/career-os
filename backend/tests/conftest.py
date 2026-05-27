"""Pytest configuration — avoid lifespan DB/scheduler startup in API tests."""

from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest

# Patched on every test so importing app.main never touches Mongo/scheduler/Redis.
_LIFECYCLE_MOCKS: tuple[str, ...] = (
    "app.main.connect_to_mongo",
    "app.main.close_mongo_connection",
    "app.main.get_redis",
    "app.main.close_redis",
    "app.main.start_scheduler",
    "app.main.shutdown_scheduler",
    "app.main.shutdown_automation",
    "app.main.start_realtime_subscriber",
    "app.main.run_legacy_data_migration",
    "app.main.seed_demo_users",
    "app.main.ensure_user_indexes",
    "app.main.ensure_workspace_indexes",
    "app.main.ensure_auth_indexes",
    "app.main.ensure_preferences_indexes",
    "app.main.ensure_scan_session_indexes",
    "app.main.ensure_job_indexes",
    "app.main.ensure_resume_indexes",
    "app.main.ensure_application_indexes",
    "app.main.ensure_notification_indexes",
    "app.main.ensure_career_insight_indexes",
    "app.main.ensure_apply_indexes",
    "app.main.ensure_prep_indexes",
    "app.main.ensure_copilot_indexes",
    "app.main.ensure_web_question_cache_indexes",
    "app.main.ensure_password_reset_indexes",
)


@pytest.fixture(autouse=True)
def _patch_lifecycle():
    """Prevent Mongo/scheduler startup during HTTP tests."""
    with ExitStack() as stack:
        for target in _LIFECYCLE_MOCKS:
            if target.endswith("get_redis") or target.endswith("close_redis"):
                stack.enter_context(patch(target))
            elif target.endswith("start_realtime_subscriber"):
                stack.enter_context(
                    patch(target, new=AsyncMock(return_value=None))
                )
            else:
                stack.enter_context(patch(target, new=AsyncMock()))
        yield
