"""Salesforce CRM adapter skeleton."""

from __future__ import annotations

from live_demo_api.config import get_settings
from live_demo_api.post_demo.crm.crm_types import (
    CrmExportRequest,
    CrmExportResult,
    CrmHealth,
    CrmPayload,
    CrmValidationResult,
)


class SalesforceCrmAdapter:
    provider_name = "salesforce"
    adapter_version = "skeleton-v1"

    async def health_check(self) -> CrmHealth:
        settings = get_settings()
        healthy = bool(
            settings.salesforce_instance_url and settings.salesforce_access_token.get_secret_value()
        )
        return CrmHealth(healthy=healthy, reason=None if healthy else "missing_salesforce_config")

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
            error_message=(
                "Salesforce export is a Phase 13 skeleton and does not send network requests."
            ),
            redacted_payload=request.payload,
            latency_ms=0,
        )
