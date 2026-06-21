from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns


@dataclass(frozen=True, slots=True)
class RecipeTiming:
    operation: str
    latency_ms: float


class RecipeTimer:
    def __init__(self, operation: str) -> None:
        self._operation = operation
        self._start = perf_counter_ns()

    def finish(self) -> RecipeTiming:
        return RecipeTiming(self._operation, (perf_counter_ns() - self._start) / 1_000_000)
