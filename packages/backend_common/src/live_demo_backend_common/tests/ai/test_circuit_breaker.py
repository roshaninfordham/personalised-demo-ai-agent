from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from live_demo_backend_common.ai.circuit_breaker import CircuitBreaker, CircuitBreakerState
from live_demo_backend_common.ai.errors import ProviderCircuitOpenError


def test_circuit_breaker_opens_half_opens_and_closes() -> None:
    breaker: CircuitBreaker = CircuitBreaker(
        provider_name="p",
        failure_threshold=2,
        cooldown_seconds=30,
    )
    breaker.record_failure(retryable=True)
    assert breaker.state == CircuitBreakerState.closed
    breaker.record_failure(retryable=True)
    assert str(breaker.state) == "open"
    with pytest.raises(ProviderCircuitOpenError):
        breaker.before_request(model_name="m", operation="op")
    breaker.opened_at = datetime.now(UTC) - timedelta(seconds=31)
    breaker.before_request(model_name="m", operation="op")
    assert str(breaker.state) == "half_open"
    breaker.record_success()
    assert breaker.state == CircuitBreakerState.closed
