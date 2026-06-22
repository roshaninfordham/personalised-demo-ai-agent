"""Webhook CRM adapter skeleton with SSRF-safe config validation."""

from __future__ import annotations

from urllib.parse import urlsplit

from live_demo_api.config import get_settings
from live_demo_api.post_demo.crm.crm_types import (
    CrmExportRequest,
    CrmExportResult,
    CrmHealth,
    CrmPayload,
    CrmValidationResult,
)
from live_demo_api.security import _is_blocked_hostname


class WebhookCrmAdapter:
    provider_name = "webhook"
    adapter_version = "skeleton-v1"

    async def health_check(self) -> CrmHealth:
        settings = get_settings()
        url = settings.crm_webhook_url
        if not url:
            return CrmHealth(healthy=False, reason="missing_webhook_url")
        parsed = urlsplit(url)
        if parsed.scheme != "https" and settings.app_env != "local":
            return CrmHealth(healthy=False, reason="webhook_requires_https")
        if (
            parsed.hostname
            and _is_blocked_hostname(parsed.hostname)
            and settings.app_env != "local"
        ):
            return CrmHealth(healthy=False, reason="webhook_private_host_blocked")
        if (
            settings.crm_webhook_signing_enabled
            and not settings.crm_webhook_secret.get_secret_value()
        ):
            return CrmHealth(healthy=False, reason="missing_webhook_secret")
        return CrmHealth(healthy=True)

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
                "Webhook export is disabled in Phase 13 and does not send network requests."
            ),
            redacted_payload=request.payload,
            latency_ms=0,
        )
