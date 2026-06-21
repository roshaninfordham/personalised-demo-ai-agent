"""Memory and lead-insight redaction helpers."""

from __future__ import annotations

from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine


class MemoryRedactor:
    def __init__(self, engine: RedactionEngine | None = None) -> None:
        self._engine = engine or RedactionEngine()

    def redact_memory_text(self, text: str) -> str:
        return str(self._engine.redact_text(text, RedactionContext.LEAD_SUMMARY).redacted_value)

