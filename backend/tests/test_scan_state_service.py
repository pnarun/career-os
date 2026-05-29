"""Scan state service tests (Mongo in-memory patch + Redis fallback)."""

from unittest.mock import patch

import pytest

from app.models.scan_state import ScanState
from app.services import cache_service, scan_state_service
from app.services import scan_state_mongo_store

_mongo_memory: dict[str, ScanState] = {}


def _patch_save(state: ScanState) -> bool:
    _mongo_memory[state.scan_id] = state.model_copy(deep=True)
    return True


def _patch_load(scan_id: str) -> ScanState | None:
    state = _mongo_memory.get(scan_id)
    return state.model_copy(deep=True) if state else None


def _patch_delete(scan_id: str) -> None:
    _mongo_memory.pop(scan_id, None)


@pytest.fixture(autouse=True)
def _reset_cache():
    _mongo_memory.clear()
    cache_service._memory_cache.clear()
    cache_service._client = None
    cache_service._client_checked = False
    with (
        patch.object(cache_service, "_cache_enabled", return_value=False),
        patch.object(scan_state_mongo_store, "save_scan_state", side_effect=_patch_save),
        patch.object(scan_state_mongo_store, "load_scan_state", side_effect=_patch_load),
        patch.object(scan_state_mongo_store, "delete_scan_state", side_effect=_patch_delete),
    ):
        yield
    _mongo_memory.clear()
    cache_service._memory_cache.clear()


def test_scan_state_lifecycle():
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
    assert state.progress > 0
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
    scan_state_service.create_scan_state(scan_id="scan_test_2", user_id="user_a")
    assert scan_state_service.get_scan_state("scan_test_2", user_id="user_b") is None


def test_active_scan_skips_redis_cache():
    scan_state_service.create_scan_state(scan_id="scan_test_3", user_id="user_a")
    scan_state_service.update_scan_progress("scan_test_3", progress=25, status="fetching")
    redis_key = "scan:state:scan_test_3"
    assert cache_service.get_json(redis_key) is None
    mongo_state = scan_state_mongo_store.load_scan_state("scan_test_3")
    assert mongo_state is not None
    assert mongo_state.progress >= 25


def test_completed_scan_writes_redis_cache():
    scan_state_service.create_scan_state(scan_id="scan_test_4", user_id="user_a")
    scan_state_service.complete_scan(
        "scan_test_4",
        jobs_stored=1,
        jobs_found=1,
        result_summary={"stored": 1},
    )
    redis_key = "scan:state:scan_test_4"
    cached = cache_service.get_json(redis_key)
    assert cached is not None
    assert cached["status"] == "completed"


def test_partial_success_in_result_summary():
    scan_state_service.create_scan_state(scan_id="scan_test_5", user_id="user_a")
    state = scan_state_service._load("scan_test_5")
    state.providers_failed.append("indeed")
    scan_state_service._save(state)
    scan_state_service.complete_scan(
        "scan_test_5",
        jobs_stored=2,
        jobs_found=5,
        result_summary={"stored": 2},
    )
    done = scan_state_service.get_scan_state("scan_test_5")
    assert done.result_summary.get("partial_success") is True
