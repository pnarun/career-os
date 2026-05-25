"""Pytest configuration — avoid lifespan DB connection in API tests."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def _patch_lifecycle():
    """Prevent Mongo/scheduler startup during HTTP tests."""
    with (
        patch("app.main.connect_to_mongo", new=AsyncMock()),
        patch("app.main.close_mongo_connection", new=AsyncMock()),
        patch("app.main.start_scheduler", new=AsyncMock()),
        patch("app.main.shutdown_scheduler", new=AsyncMock()),
        patch("app.main.shutdown_automation", new=AsyncMock()),
        patch("app.main.start_realtime_subscriber", new=AsyncMock(return_value=None)),
        patch("app.main.run_legacy_data_migration", new=AsyncMock()),
        patch("app.main.seed_demo_users", new=AsyncMock()),
        patch("app.main.ensure_user_indexes", new=AsyncMock()),
        patch("app.main.ensure_workspace_indexes", new=AsyncMock()),
        patch("app.main.ensure_auth_indexes", new=AsyncMock()),
        patch("app.main.ensure_preferences_indexes", new=AsyncMock()),
        patch("app.main.ensure_scan_session_indexes", new=AsyncMock()),
        patch("app.main.ensure_job_indexes", new=AsyncMock()),
        patch("app.main.ensure_application_indexes", new=AsyncMock()),
        patch("app.main.ensure_notification_indexes", new=AsyncMock()),
        patch("app.main.ensure_career_insight_indexes", new=AsyncMock()),
        patch("app.main.ensure_apply_indexes", new=AsyncMock()),
        patch("app.main.ensure_prep_indexes", new=AsyncMock()),
        patch("app.main.ensure_copilot_indexes", new=AsyncMock()),
        patch("app.main.ensure_web_question_cache_indexes", new=AsyncMock()),
        patch("app.main.ensure_password_reset_indexes", new=AsyncMock()),
    ):
        yield
