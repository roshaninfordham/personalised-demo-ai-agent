# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: E501, F401, RUF100

from __future__ import annotations

from enum import StrEnum
from typing import Literal

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


class PostDemoJobType(StrEnum):
    EXTRACT_LEAD_INSIGHTS = "extract_lead_insights"
    TRACK_FEATURES_SHOWN = "track_features_shown"
    GENERATE_LEAD_SUMMARY = "generate_lead_summary"
    EXPORT_CRM_PAYLOAD = "export_crm_payload"
    RUN_FULL_POST_DEMO_INTELLIGENCE = "run_full_post_demo_intelligence"


class PostDemoRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_mode: str = "full"
    export_crm: bool = False
    crm_provider: str = "mock"


class PostDemoRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UuidString
    status: str
    lead_summary_id: UuidString | None
    crm_export_id: UuidString | None
