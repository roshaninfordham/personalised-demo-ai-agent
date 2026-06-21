"""Demo graph confidence math."""

from __future__ import annotations


def laplace_confidence(success_count: int, failure_count: int) -> float:
    return round((success_count + 1) / (success_count + failure_count + 2), 3)


def incremental_average(old_average: int | None, old_count: int, new_value: int) -> int:
    if old_average is None or old_count <= 0:
        return new_value
    return round(old_average + (new_value - old_average) / (old_count + 1))
