"""Demo graph data structures."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DemoGraphScreenNode:
    screen_id: UUID
    product_id: UUID
    screen_hash: str
    url_path: str | None
    title: str | None
    summary: str | None
    screen_type: str | None
    features: tuple[str, ...]
    risk_level: str
    confidence: float


@dataclass(frozen=True, slots=True)
class DemoGraphActionEdge:
    edge_id: UUID
    product_id: UUID
    from_screen_id: UUID
    to_screen_id: UUID | None
    action_type: str
    action_label: str | None
    element_fingerprint: str | None
    risk_level: str
    success_count: int
    failure_count: int
    average_latency_ms: int | None
    confidence: float
