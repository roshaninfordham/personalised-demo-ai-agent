"""Mock CRM adapter."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Literal

from live_demo_api.config import get_settings
from live_demo_api.post_demo.crm.crm_redaction import redact_crm_payload
from live_demo_api.post_demo.crm.crm_types import (
    CrmExportRequest,
    CrmExportResult,
    CrmHealth,
    CrmPayload,
    CrmValidationResult,
)


class MockCrmAdapter:
    provider_name = "mock"
    adapter_version = "v1"

    async def health_check(self) -> CrmHealth:
        return CrmHealth(healthy=True)

    async def validate_payload(self, payload: CrmPayload) -> CrmValidationResult:
        required = {"schema_version", "session_id", "product_id", "lead", "demo", "qualification"}
        missing = sorted(required - set(payload))
        return CrmValidationResult(
            valid=not missing,
            errors=tuple(f"missing:{item}" for item in missing),
        )

    async def export(self, request: CrmExportRequest) -> CrmExportResult:
        start = perf_counter()
        settings = get_settings()
        redacted, _ = redact_crm_payload(request.payload)
        if settings.mock_crm_fail_export:
            return CrmExportResult(
                provider=self.provider_name,
                status="failed",
                external_object_ids={},
                error_code="mock_crm_failure",
                error_message="Mock CRM failure requested by configuration.",
                redacted_payload=redacted,
                latency_ms=round((perf_counter() - start) * 1000),
            )
        output_dir = Path(settings.mock_crm_output_dir)
        path = output_dir / f"{request.session_id}-{request.idempotency_key[:12]}.json"
        await asyncio.to_thread(_write_export_file, path, redacted)
        status: Literal["sent", "dry_run_completed"] = (
            "dry_run_completed" if request.dry_run else "sent"
        )
        return CrmExportResult(
            provider=self.provider_name,
            status=status,
            external_object_ids=_mock_ids(str(request.session_id)),
            error_code=None,
            error_message=None,
            redacted_payload=redacted,
            latency_ms=round((perf_counter() - start) * 1000),
        )


def _mock_ids(session_id: str) -> dict[str, str]:
    return {
        name: f"mock_{name}_{hashlib.sha256(f'{session_id}:{name}'.encode()).hexdigest()[:12]}"
        for name in ("contact", "company", "deal", "note")
    }


def _write_export_file(path: Path, payload: CrmPayload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
