"""Custom CRM adapter skeleton."""

from __future__ import annotations

from live_demo_api.post_demo.crm.crm_types import (
    CrmExportRequest,
    CrmExportResult,
    CrmHealth,
    CrmPayload,
    CrmValidationResult,
)


class CustomCrmAdapter:
    provider_name = "custom"
    adapter_version = "skeleton-v1"

    async def health_check(self) -> CrmHealth:
        return CrmHealth(healthy=False, reason="not_implemented")

    async def validate_payload(self, payload: CrmPayload) -> CrmValidationResult:
        return CrmValidationResult(
            valid=bool(payload),
            errors=() if payload else ("empty_payload",),
        )

    async def export(self, request: CrmExportRequest) -> CrmExportResult:
        return CrmExportResult(
            provider=self.provider_name,
            status="skipped",
            external_object_ids={},
            error_code="not_implemented",
            error_message="Custom CRM adapter is a Phase 13 skeleton.",
            redacted_payload=request.payload,
            latency_ms=0,
        )
