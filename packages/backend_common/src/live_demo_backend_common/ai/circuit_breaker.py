from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from live_demo_backend_common.ai.errors import ProviderCircuitOpenError


class CircuitBreakerState(StrEnum):
    closed = "closed"
    open = "open"
    half_open = "half_open"


@dataclass(slots=True)
class CircuitBreaker:
    provider_name: str
    failure_threshold: int = 5
    cooldown_seconds: int = 30
    state: CircuitBreakerState = CircuitBreakerState.closed
    consecutive_failures: int = 0
    opened_at: datetime | None = None

    def before_request(self, *, model_name: str | None, operation: str) -> None:
        if self.state != CircuitBreakerState.open:
            return
        assert self.opened_at is not None
        if datetime.now(UTC) - self.opened_at >= timedelta(seconds=self.cooldown_seconds):
            self.state = CircuitBreakerState.half_open
            return
        raise ProviderCircuitOpenError(
            provider_name=self.provider_name,
            model_name=model_name,
            operation=operation,
            retryable=True,
            status_code=None,
            safe_message="Provider circuit breaker is open.",
        )

    def record_success(self) -> None:
        self.state = CircuitBreakerState.closed
        self.consecutive_failures = 0
        self.opened_at = None

    def record_failure(self, *, retryable: bool) -> None:
        if not retryable:
            return
        if self.state == CircuitBreakerState.half_open:
            self._open()
            return
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self._open()

    def _open(self) -> None:
        self.state = CircuitBreakerState.open
        self.opened_at = datetime.now(UTC)
