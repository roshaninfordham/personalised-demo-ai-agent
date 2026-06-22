"""Combined post-demo insight extractor."""

from __future__ import annotations

from live_demo_api.config import get_settings
from live_demo_api.post_demo.evidence.evidence_index import EvidenceIndex
from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.insights.deterministic_insight_extractor import (
    DeterministicInsightExtractor,
)
from live_demo_api.post_demo.insights.insight_deduper import dedupe_insights
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight
from live_demo_api.post_demo.insights.llm_insight_extractor import LlmInsightExtractor


class LeadInsightExtractor:
    def __init__(
        self,
        deterministic: DeterministicInsightExtractor | None = None,
        llm: LlmInsightExtractor | None = None,
    ) -> None:
        self._deterministic = deterministic or DeterministicInsightExtractor()
        self._llm = llm or LlmInsightExtractor()

    def extract(
        self,
        bundle: SessionEvidenceBundle,
        *,
        llm_candidates: list[dict[str, object]] | None = None,
    ) -> tuple[ExtractedLeadInsight, ...]:
        settings = get_settings()
        deterministic = self._deterministic.extract(bundle)
        candidates: tuple[ExtractedLeadInsight, ...] = ()
        if settings.lead_insight_use_llm and llm_candidates:
            candidates = self._llm.validate_candidates(llm_candidates, EvidenceIndex.build(bundle))
        merged = dedupe_insights(deterministic + candidates)
        return tuple(
            insight
            for insight in merged
            if insight.confidence >= settings.lead_insight_min_confidence
            and insight.importance >= settings.lead_insight_min_importance
        )
