"""Deterministic lead insight extractor."""

from __future__ import annotations

from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.insights.buying_signal_detector import detect_buying_signals
from live_demo_api.post_demo.insights.feature_interest_detector import detect_feature_interests
from live_demo_api.post_demo.insights.insight_deduper import dedupe_insights
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight
from live_demo_api.post_demo.insights.objection_detector import detect_objections
from live_demo_api.post_demo.insights.pain_point_detector import detect_pain_points
from live_demo_api.post_demo.insights.role_detector import detect_roles
from live_demo_api.post_demo.insights.unanswered_question_detector import (
    detect_unanswered_questions,
)
from live_demo_api.post_demo.insights.urgency_detector import detect_urgency


class DeterministicInsightExtractor:
    def extract(self, bundle: SessionEvidenceBundle) -> tuple[ExtractedLeadInsight, ...]:
        insights: list[ExtractedLeadInsight] = []
        insights.extend(detect_roles(bundle))
        insights.extend(detect_pain_points(bundle))
        insights.extend(detect_objections(bundle))
        insights.extend(detect_buying_signals(bundle))
        insights.extend(detect_urgency(bundle))
        insights.extend(detect_feature_interests(bundle))
        insights.extend(detect_unanswered_questions(bundle))
        return tuple(dedupe_insights(tuple(insights)))
