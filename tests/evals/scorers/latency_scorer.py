from __future__ import annotations

from collections.abc import Mapping


def score_latency(
    case: Mapping[str, object], *, threshold_ms: float = 1500
) -> dict[str, float | bool]:
    latency = case.get("latency_ms")
    value = float(latency) if isinstance(latency, int | float) else 0.0
    return {"passed": value <= threshold_ms, "latency_ms": value}
