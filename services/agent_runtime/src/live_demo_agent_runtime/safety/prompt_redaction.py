"""Prompt redaction helpers for agent-brain context construction."""

from __future__ import annotations

from typing import Any

from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine


class PromptRedactor:
    def __init__(self, engine: RedactionEngine | None = None) -> None:
        self._engine = engine or RedactionEngine()

    def redact_text(self, text: str) -> str:
        return str(self._engine.redact_text(text, RedactionContext.PROMPT).redacted_value)

    def redact_context(self, value: Any) -> Any:
        return self._engine.redact_json(value, RedactionContext.PROMPT).redacted_value

