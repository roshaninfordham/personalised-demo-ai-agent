"""CRM adapter interface."""

from __future__ import annotations

from typing import Protocol

from live_demo_api.post_demo.crm.crm_types import (
    CrmExportRequest,
    CrmExportResult,
    CrmHealth,
    CrmPayload,
    CrmValidationResult,
)


class CrmAdapter(Protocol):
    provider_name: str
    adapter_version: str

    async def health_check(self) -> CrmHealth: ...

    async def validate_payload(self, payload: CrmPayload) -> CrmValidationResult: ...

    async def export(self, request: CrmExportRequest) -> CrmExportResult: ...
