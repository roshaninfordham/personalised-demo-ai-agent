"""Latency budget checks and observation helpers."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

from live_demo_backend_common.observability import metric_names
from live_demo_backend_common.observability.latency_budget import (
    DEFAULT_LATENCY_BUDGETS,
    LatencyBudget,
)
from live_demo_backend_common.observability.log_events import LATENCY_BUDGET_VIOLATION
from live_demo_backend_common.observability.logging import log_event
from live_demo_backend_common.observability.metrics import MetricRegistry, get_global_registry
from live_demo_backend_common.observability.tracing import add_span_event

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class LatencyCheckResult:
    operation: str
    duration_ms: float
    status: str
    severity: str
    target_ms: float
    excess_ms: float


class LatencyEnforcer:
    def __init__(
        self,
        *,
        budgets: Mapping[str, LatencyBudget] | None = None,
        metrics: MetricRegistry | None = None,
        enabled: bool = True,
    ) -> None:
        self._budgets = dict(budgets or DEFAULT_LATENCY_BUDGETS)
        self._metrics = metrics or get_global_registry()
        self._enabled = enabled
        self._critical_counts: dict[tuple[str, str, str], tuple[int, float]] = {}

    def check(
        self,
        operation: str,
        duration_ms: float,
        *,
        context: Mapping[str, object] | None = None,
    ) -> LatencyCheckResult:
        budget = self._budgets.get(operation)
        if not self._enabled or budget is None or not budget.enabled:
            return LatencyCheckResult(operation, duration_ms, "disabled", "none", 0, 0)
        status, severity = _classify(duration_ms, budget)
        excess_ms = max(0.0, duration_ms - budget.target_ms)
        self._metrics.increment(
            metric_names.LATENCY_BUDGET_CHECKS_TOTAL,
            labels={"operation": operation, "status": status},
        )
        if severity in {"warning", "violated", "critical"}:
            self._metrics.increment(
                metric_names.LATENCY_BUDGET_VIOLATIONS_TOTAL,
                labels={"operation": operation, "severity": severity},
            )
            self._metrics.observe(
                metric_names.LATENCY_BUDGET_EXCESS_SECONDS,
                excess_ms / 1000,
                labels={"operation": operation, "severity": severity},
            )
            payload = {
                "operation": operation,
                "duration_ms": round(duration_ms, 3),
                "target_ms": budget.target_ms,
                "warning_ms": budget.warning_ms,
                "critical_ms": budget.critical_ms,
                "severity": severity,
                "excess_ms": round(excess_ms, 3),
                **dict(context or {}),
            }
            add_span_event("latency_budget.violation", payload)
            log_event(
                LOGGER,
                event_type=LATENCY_BUDGET_VIOLATION,
                message="Latency budget exceeded.",
                level=logging.WARNING if severity != "critical" else logging.ERROR,
                component="latency_enforcer",
                success=False,
                latency_ms=round(duration_ms, 3),
                **payload,
            )
            if severity == "critical" and budget.hot_path:
                self._record_critical(operation, context or {})
        return LatencyCheckResult(
            operation=operation,
            duration_ms=duration_ms,
            status=status,
            severity=severity,
            target_ms=budget.target_ms,
            excess_ms=excess_ms,
        )

    def is_session_degraded(self, session_id: str, operation: str) -> bool:
        key = (session_id, operation, "critical")
        count, expires_at = self._critical_counts.get(key, (0, 0))
        if time.monotonic() > expires_at:
            return False
        return count >= 3

    def _record_critical(self, operation: str, context: Mapping[str, object]) -> None:
        session_id = str(context.get("session_id") or "")
        if not session_id:
            return
        key = (session_id, operation, "critical")
        now = time.monotonic()
        count, expires_at = self._critical_counts.get(key, (0, 0))
        if now > expires_at:
            count = 0
        self._critical_counts[key] = (count + 1, now + 60)


@contextmanager
def latency_observer(
    operation: str,
    *,
    enforcer: LatencyEnforcer | None = None,
    context: Mapping[str, object] | None = None,
) -> Iterator[None]:
    start_ns = time.perf_counter_ns()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        (enforcer or LatencyEnforcer()).check(operation, elapsed_ms, context=context)


@asynccontextmanager
async def async_latency_observer(
    operation: str,
    *,
    enforcer: LatencyEnforcer | None = None,
    context: Mapping[str, object] | None = None,
) -> AsyncIterator[None]:
    start_ns = time.perf_counter_ns()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        (enforcer or LatencyEnforcer()).check(operation, elapsed_ms, context=context)


def _classify(duration_ms: float, budget: LatencyBudget) -> tuple[str, str]:
    if duration_ms <= budget.target_ms:
        return "ok", "none"
    if duration_ms <= budget.warning_ms:
        return "warning", "warning"
    if duration_ms <= budget.critical_ms:
        return "violated", "violated"
    return "critical", "critical"
