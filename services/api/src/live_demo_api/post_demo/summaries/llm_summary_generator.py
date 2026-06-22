"""Optional LLM summary wording hook."""

from __future__ import annotations

from typing import Any

from live_demo_api.post_demo.summaries.summary_validator import SummaryValidator


class LlmSummaryGenerator:
    def validate_or_fallback(
        self, candidate: dict[str, Any] | None, fallback: dict[str, Any]
    ) -> dict[str, Any]:
        if candidate is None:
            return fallback
        return candidate if SummaryValidator().validate(candidate) else fallback
