"""Cache layer tests."""

from app.core.cache import cache_delete, cache_get, cache_set


def test_memory_cache_fallback():
    key = "test:cache:key"
    cache_delete(key)
    cache_set(key, {"value": 42}, ttl_seconds=60)
    assert cache_get(key) == {"value": 42}
    cache_delete(key)
    assert cache_get(key) is None
