"""CRM export datatypes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

CrmPayload = dict[str, Any]


@dataclass(frozen=True, slots=True)
class CrmHealth:
    healthy: bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class CrmValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CrmExportRequest:
    organization_id: UUID
    session_id: UUID
    lead_summary_id: UUID
    payload: CrmPayload
    dry_run: bool
    idempotency_key: str
    trace_id: str


@dataclass(frozen=True, slots=True)
class CrmExportResult:
    provider: str
    status: Literal["sent", "failed", "skipped", "dry_run_completed"]
    external_object_ids: dict[str, str]
    error_code: str | None
    error_message: str | None
    redacted_payload: dict[str, Any]
    latency_ms: int
