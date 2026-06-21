"""Learner-specific redaction helpers."""

from __future__ import annotations

from live_demo_backend_common.policy.policy_types import RedactionResult
from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine


class LearnerRedactor:
    def __init__(self, engine: RedactionEngine) -> None:
        self._engine = engine

    def redact_for_summary(self, text: str) -> RedactionResult:
        return self._engine.redact_text(text, RedactionContext.SCREEN_SUMMARY)

    def redact_for_prompt(self, text: str) -> RedactionResult:
        return self._engine.redact_text(text, RedactionContext.PROMPT)

    def redact_for_embedding(self, text: str) -> RedactionResult:
        return self._engine.redact_text(text, RedactionContext.KNOWLEDGE_CHUNK)
