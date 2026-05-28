"""Scan state service tests (in-memory Redis fallback)."""

from unittest.mock import patch

import pytest

from app.services import cache_service, scan_state_service


@pytest.fixture(autouse=True)
def _reset_cache():
    cache_service._memory_cache.clear()
    cache_service._client = None
    cache_service._client_checked = False
    yield
    cache_service._memory_cache.clear()


def test_scan_state_lifecycle():
    with patch.object(cache_service, "_cache_enabled", return_value=False):
        scan_state_service.create_scan_state(scan_id="scan_test_1", user_id="user_a")
        scan_state_service.mark_provider_running("scan_test_1", "naukri")
        scan_state_service.update_scan_progress_provider(
            "scan_test_1",
            "naukri",
            status="success",
            jobs_found=5,
        )
        state = scan_state_service.get_scan_state("scan_test_1", user_id="user_a")
        assert state is not None
        assert "naukri" in state.providers_completed
        assert state.providers["naukri"].jobs_found == 5

        scan_state_service.complete_scan(
            "scan_test_1",
            jobs_stored=3,
            jobs_found=10,
            result_summary={"stored": 3},
        )
        done = scan_state_service.get_scan_state("scan_test_1")
        assert done.status == "completed"
        assert done.progress == 100
        assert done.result_summary == {"stored": 3}


def test_scan_state_user_isolation():
    with patch.object(cache_service, "_cache_enabled", return_value=False):
        scan_state_service.create_scan_state(scan_id="scan_test_2", user_id="user_a")
        assert scan_state_service.get_scan_state("scan_test_2", user_id="user_b") is None
