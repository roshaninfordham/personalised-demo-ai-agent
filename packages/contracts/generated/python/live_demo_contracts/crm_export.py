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


class CrmExportStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"
    DRY_RUN_COMPLETED = "dry_run_completed"


class CrmExportRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crm_export_id: UuidString
    provider: str
    status: CrmExportStatus
    dry_run: bool
    external_object_ids: Metadata
    created_at: IsoDateTimeString


class CrmExportsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CrmExportRecord] = Field(default_factory=list)
