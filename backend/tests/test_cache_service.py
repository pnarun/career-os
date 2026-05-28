"""Unit tests for Upstash cache service (in-memory fallback)."""

from unittest.mock import patch

import pytest

from app.services import cache_service


@pytest.fixture(autouse=True)
def _reset_cache_state():
    cache_service._client = None
    cache_service._client_checked = False
    cache_service._client_connected = False
    cache_service._memory_cache.clear()
    yield
    cache_service._memory_cache.clear()


def test_get_set_json_memory_fallback():
    with patch.object(cache_service, "_cache_enabled", return_value=False):
        assert cache_service.get_json("test:key") is None
        cache_service.set_json("test:key", {"a": 1}, 60)
        assert cache_service.get_json("test:key") == {"a": 1}


def test_delete_and_exists_memory():
    with patch.object(cache_service, "_cache_enabled", return_value=False):
        cache_service.set_json("del:key", [1], 60)
        assert cache_service.exists("del:key") is True
        cache_service.delete("del:key")
        assert cache_service.exists("del:key") is False


def test_is_connected_without_credentials():
    with patch.object(cache_service.settings, "UPSTASH_REDIS_REST_URL", ""):
        with patch.object(cache_service.settings, "UPSTASH_REDIS_REST_TOKEN", ""):
            assert cache_service.is_connected() is False
