"""Circuit breaker unit tests."""

from app.core.circuit_breaker import (
    is_provider_circuit_open,
    record_provider_failure,
    record_provider_success,
)


def test_circuit_opens_after_threshold():
    provider = "test_provider_cb"
    record_provider_success(provider)
    for _ in range(5):
        record_provider_failure(provider, threshold=5, cooldown_seconds=60)
    assert is_provider_circuit_open(provider) is True


def test_circuit_closes_after_success():
    provider = "test_provider_reset"
    for _ in range(5):
        record_provider_failure(provider, threshold=5, cooldown_seconds=60)
    record_provider_success(provider)
    assert is_provider_circuit_open(provider) is False
