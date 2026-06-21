"""Small monotonic latency recorder."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(slots=True)
class LearnerMetrics:
    timings_ms: dict[str, float] = field(default_factory=dict)

    def timer(self, name: str) -> MetricTimer:
        return MetricTimer(self, name)


class MetricTimer:
    def __init__(self, metrics: LearnerMetrics, name: str) -> None:
        self._metrics = metrics
        self._name = name
        self._started_ns = 0

    def __enter__(self) -> MetricTimer:
        self._started_ns = time.perf_counter_ns()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        elapsed = (time.perf_counter_ns() - self._started_ns) / 1_000_000
        self._metrics.timings_ms[self._name] = elapsed
