from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PolicyTiming:
    operation: str
    latency_ms: float
