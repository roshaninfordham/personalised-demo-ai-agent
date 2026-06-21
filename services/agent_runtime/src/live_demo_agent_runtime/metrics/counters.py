"""Simple in-process counters for bounded backpressure metrics."""

from collections import Counter


class RuntimeCounters:
    def __init__(self) -> None:
        self._counter: Counter[str] = Counter()

    def increment(self, name: str, amount: int = 1) -> None:
        self._counter[name] += amount

    def snapshot(self) -> dict[str, int]:
        return dict(self._counter)
