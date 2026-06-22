"""CRM export service and adapter registry."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import CrmExport, DemoSession, LeadSummary, Product
from live_demo_api.post_demo.crm.crm_adapter import CrmAdapter
from live_demo_api.post_demo.crm.crm_payload_mapper import CrmPayloadMapper
from live_demo_api.post_demo.crm.crm_types import CrmExportRequest, CrmExportResult
from live_demo_api.post_demo.crm.custom_adapter import CustomCrmAdapter
from live_demo_api.post_demo.crm.hubspot_adapter import HubSpotCrmAdapter
from live_demo_api.post_demo.crm.mock_crm_adapter import MockCrmAdapter
from live_demo_api.post_demo.crm.salesforce_adapter import SalesforceCrmAdapter
from live_demo_api.post_demo.crm.webhook_adapter import WebhookCrmAdapter
from live_demo_api.post_demo.post_demo_errors import CrmConfigurationError
from live_demo_api.post_demo.repositories.crm_exports import CrmExportRepository


class CrmAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, CrmAdapter] = {
            "mock": MockCrmAdapter(),
            "hubspot": HubSpotCrmAdapter(),
            "salesforce": SalesforceCrmAdapter(),
            "webhook": WebhookCrmAdapter(),
            "custom": CustomCrmAdapter(),
        }

    def get_adapter(self, provider: str) -> CrmAdapter:
        try:
            return self._adapters[provider]
        except KeyError as exc:
            raise CrmConfigurationError(f"Unsupported CRM provider: {provider}") from exc


class CrmExportService:
    def __init__(self, registry: CrmAdapterRegistry | None = None) -> None:
        self._registry = registry or CrmAdapterRegistry()
        self._mapper = CrmPayloadMapper()

    async def export(
        self,
        db: AsyncSession,
        *,
        organization_id: object,
        session: DemoSession,
        product: Product,
        lead_summary: LeadSummary,
        provider: str,
        dry_run: bool,
        trace_id: str,
    ) -> tuple[CrmExportResult, CrmExport]:
        payload = self._mapper.map_payload(
            lead_summary=lead_summary, session=session, product=product
        )
        metadata = payload.setdefault("metadata", {})
        if isinstance(metadata, dict):
            metadata["dry_run"] = dry_run
        adapter = self._registry.get_adapter(provider)
        redacted_hash = payload_hash(payload)
        request = CrmExportRequest(
            organization_id=session.organization_id,
            session_id=session.session_id,
            lead_summary_id=lead_summary.lead_summary_id,
            payload=payload,
            dry_run=dry_run,
            idempotency_key=f"crm_export:{provider}:{session.session_id}:{lead_summary.lead_summary_id}:{redacted_hash}",
            trace_id=trace_id,
        )
        result = await adapter.export(request)
        row = await CrmExportRepository(db).upsert_result(
            organization_id=session.organization_id,
            session_id=session.session_id,
            lead_summary_id=lead_summary.lead_summary_id,
            provider=provider,
            payload=payload,
            result=result,
            dry_run=dry_run,
            idempotency_key=request.idempotency_key,
        )
        return result, row


def payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
