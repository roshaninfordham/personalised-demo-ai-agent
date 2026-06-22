# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: E501, F401, RUF100

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

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


class GenericCrmPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "v1"
    session_id: UuidString
    product_id: UuidString
    lead: Metadata
    demo: Metadata
    qualification: Metadata
    recommended_follow_up: Metadata
    evidence: Metadata
    metadata: Metadata
