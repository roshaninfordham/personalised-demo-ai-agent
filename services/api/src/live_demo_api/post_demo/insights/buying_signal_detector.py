"""Buying signal detector."""

from __future__ import annotations

from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.insights.insight_scoring import evidence_strength, score_importance
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight, normalize_content

BUYING_PATTERNS = (
    "pricing",
    "setup",
    "integration",
    "team rollout",
    "export",
    "next steps",
    "trial",
    "who uses it",
    "implementation timeline",
)


def detect_buying_signals(bundle: SessionEvidenceBundle) -> list[ExtractedLeadInsight]:
    insights: list[ExtractedLeadInsight] = []
    for event in bundle.transcript_events:
        if event.speaker != "user":
            continue
        normalized = normalize_content(event.text)
        if not any(pattern in normalized for pattern in BUYING_PATTERNS):
            continue
        if "?" not in event.text and "next steps" not in normalized and "trial" not in normalized:
            continue
        ids = (event.transcript_event_id,)
        content = f"User asked about {event.text.strip().rstrip('?').rstrip('.')}."
        confidence = 0.65
        importance = score_importance(
            insight_type="buying_signal",
            confidence=confidence,
            specificity=0.75,
            recency=0.8,
            evidence_strength_value=evidence_strength(transcript_ids=ids),
        )
        insights.append(
            ExtractedLeadInsight(
                insight_type="buying_signal",
                content=content,
                normalized_content=normalize_content(content),
                confidence=confidence,
                importance=importance,
                evidence_transcript_event_ids=ids,
                evidence_browser_action_ids=(),
                evidence_screen_ids=(),
                evidence_recipe_step_ids=(),
                extraction_method="deterministic_buying_signal",
                reason="Matched buying-signal question or next-step language.",
            )
        )
    return insights
