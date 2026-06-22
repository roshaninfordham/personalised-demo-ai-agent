"""Final lead summary generator."""

from __future__ import annotations

from typing import Any

from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.features.feature_types import FeatureCandidate
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight
from live_demo_api.post_demo.summaries.deterministic_summary_generator import (
    DeterministicSummaryGenerator,
)
from live_demo_api.post_demo.summaries.llm_summary_generator import LlmSummaryGenerator
from live_demo_api.post_demo.summaries.summary_redaction import redact_summary
from live_demo_api.post_demo.summaries.summary_validator import SummaryValidator


class LeadSummaryGenerator:
    def __init__(self) -> None:
        self._deterministic = DeterministicSummaryGenerator()
        self._llm = LlmSummaryGenerator()
        self._validator = SummaryValidator()

    def generate(
        self,
        *,
        bundle: SessionEvidenceBundle,
        insights: tuple[ExtractedLeadInsight, ...],
        features: tuple[FeatureCandidate, ...],
        llm_candidate: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        deterministic = self._deterministic.generate(
            bundle=bundle, insights=insights, features=features
        )
        summary = self._llm.validate_or_fallback(llm_candidate, deterministic)
        if not self._validator.validate(summary):
            summary = deterministic
        return redact_summary(summary)
