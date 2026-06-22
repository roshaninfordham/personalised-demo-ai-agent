"""Objection detector."""

from __future__ import annotations

from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.insights.insight_scoring import evidence_strength, score_importance
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight, normalize_content

OBJECTION_PATTERNS = (
    "too expensive",
    "not sure",
    "concerned about",
    "worry about",
    "how secure",
    "setup time",
    "migration",
    "accuracy",
    "trust",
    "integration",
    "will this work with",
    "we already use",
)


def detect_objections(bundle: SessionEvidenceBundle) -> list[ExtractedLeadInsight]:
    insights: list[ExtractedLeadInsight] = []
    for event in bundle.transcript_events:
        if event.speaker != "user":
            continue
        normalized = normalize_content(event.text)
        if not any(pattern in normalized for pattern in OBJECTION_PATTERNS):
            continue
        content = event.text.strip().rstrip(".") + "."
        ids = (event.transcript_event_id,)
        confidence = 0.72
        importance = score_importance(
            insight_type="objection",
            confidence=confidence,
            specificity=0.8,
            recency=0.8,
            evidence_strength_value=evidence_strength(transcript_ids=ids),
        )
        insights.append(
            ExtractedLeadInsight(
                insight_type="objection",
                content=content,
                normalized_content=normalize_content(content),
                confidence=confidence,
                importance=importance,
                evidence_transcript_event_ids=ids,
                evidence_browser_action_ids=(),
                evidence_screen_ids=(),
                evidence_recipe_step_ids=(),
                extraction_method="deterministic_objection",
                reason="Matched objection language.",
            )
        )
    return insights
