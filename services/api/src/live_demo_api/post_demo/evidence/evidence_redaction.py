"""Redaction helpers for evidence prompts and summaries."""

from __future__ import annotations

from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine


def redact_prompt_text(text: str, engine: RedactionEngine | None = None) -> str:
    result = (engine or RedactionEngine()).redact_text(text, RedactionContext.PROMPT)
    return str(result.redacted_value)


def redact_lead_summary(value: object, engine: RedactionEngine | None = None) -> object:
    result = (engine or RedactionEngine()).redact_json(
        value,
        RedactionContext.LEAD_SUMMARY,
    )
    return result.redacted_value
