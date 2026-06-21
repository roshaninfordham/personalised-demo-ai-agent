# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: E501, F401, RUF100

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from live_demo_contracts.common import (
    BoundingBox,
    DemoPhase,
    IsoDateTimeString,
    JsonValue,
    Metadata,
    PolicyDecision,
    ProviderName,
    RiskLevel,
    SessionStatus,
    TraceId,
    UuidString,
)


class LearnerJobEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    organization_id: str
    product_id: str
    session_id: str | None | None = None
    learning_run_id: str
    job_type: Literal["learn_product_from_url", "summarize_first_screen", "explore_candidate_actions", "build_demo_graph", "generate_demo_route", "chunk_product_knowledge", "embed_knowledge_chunks", "refresh_product_learning"]
    start_url: str
    priority: int = 50
    attempt: int
    max_attempts: int
    created_at: str
    trace_id: str
    payload: dict[str, JsonValue] = Field(default_factory=dict)
