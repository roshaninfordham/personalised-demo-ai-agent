"""CRM payload redaction."""

from __future__ import annotations

from typing import Any

from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine


def redact_crm_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    result = RedactionEngine().redact_json(payload, RedactionContext.CRM_PAYLOAD)
    redacted = result.redacted_value
    return (redacted if isinstance(redacted, dict) else payload), result.applied
