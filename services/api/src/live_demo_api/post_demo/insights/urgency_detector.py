"""Urgency detector."""

from __future__ import annotations

from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.insights.insight_scoring import evidence_strength, score_importance
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight, normalize_content

URGENCY_SIGNALS = {
    "high": ("as soon as possible", "urgent", "blocked", "board meeting", "quarter end"),
    "medium": ("this week", "this month", "deadline", "launch"),
    "low": ("eventually", "later", "someday"),
}


def detect_urgency(bundle: SessionEvidenceBundle) -> list[ExtractedLeadInsight]:
    for level, signals in URGENCY_SIGNALS.items():
        for event in bundle.transcript_events:
            if event.speaker != "user":
                continue
            normalized = normalize_content(event.text)
            if not any(signal in normalized for signal in signals):
                continue
            score = {"high": 0.86, "medium": 0.62, "low": 0.35}[level]
            ids = (event.transcript_event_id,)
            content = f"Urgency appears {level}: {event.text.strip().rstrip('.')}."
            importance = score_importance(
                insight_type="urgency",
                confidence=score,
                specificity=0.8,
                recency=0.8,
                evidence_strength_value=evidence_strength(transcript_ids=ids),
            )
            return [
                ExtractedLeadInsight(
                    insight_type="urgency",
                    content=content,
                    normalized_content=normalize_content(content),
                    confidence=score,
                    importance=importance,
                    evidence_transcript_event_ids=ids,
                    evidence_browser_action_ids=(),
                    evidence_screen_ids=(),
                    evidence_recipe_step_ids=(),
                    extraction_method="deterministic_urgency",
                    reason=f"Matched {level} urgency signal.",
                )
            ]
    return []
