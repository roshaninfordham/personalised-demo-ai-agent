"""Small monotonic timer utilities for orchestration metrics."""

from __future__ import annotations

import time


def perf_counter_ns() -> int:
    return time.perf_counter_ns()


def elapsed_ms(start_ns: int) -> int:
    return int((time.perf_counter_ns() - start_ns) / 1_000_000)
