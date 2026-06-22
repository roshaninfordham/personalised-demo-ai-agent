"""Lead summary redaction."""

from __future__ import annotations

from typing import Any

from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine


def redact_summary(summary: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    result = RedactionEngine().redact_json(summary, RedactionContext.LEAD_SUMMARY)
    redacted = result.redacted_value
    if isinstance(redacted, dict):
        redaction = redacted.setdefault("redaction", {})
        if isinstance(redaction, dict):
            redaction["redaction_applied"] = result.applied
            redaction["visual_redaction_applied"] = False
    return (redacted if isinstance(redacted, dict) else summary), result.applied
