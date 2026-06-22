"""Pain point detector."""

from __future__ import annotations

from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.insights.insight_scoring import evidence_strength, score_importance
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight, normalize_content

PAIN_PATTERNS = (
    "hard to",
    "struggling with",
    "takes too long",
    "manual",
    "slow",
    "confusing",
    "can't see",
    "lack of",
    "we don't know",
    "problem is",
    "pain is",
    "challenge is",
)


def detect_pain_points(bundle: SessionEvidenceBundle) -> list[ExtractedLeadInsight]:
    insights: list[ExtractedLeadInsight] = []
    for event in bundle.transcript_events:
        if event.speaker != "user":
            continue
        normalized = normalize_content(event.text)
        if not any(pattern.replace("'", "") in normalized for pattern in PAIN_PATTERNS):
            continue
        content = _concise_pain(event.text)
        evidence_ids = (event.transcript_event_id,)
        confidence = 0.78 if "takes too long" in normalized else 0.66
        importance = score_importance(
            insight_type="pain_point",
            confidence=confidence,
            specificity=min(1.0, len(normalized.split()) / 12),
            recency=0.8,
            evidence_strength_value=evidence_strength(transcript_ids=evidence_ids),
        )
        insights.append(
            ExtractedLeadInsight(
                insight_type="pain_point",
                content=content,
                normalized_content=normalize_content(content),
                confidence=confidence,
                importance=importance,
                evidence_transcript_event_ids=evidence_ids,
                evidence_browser_action_ids=(),
                evidence_screen_ids=(),
                evidence_recipe_step_ids=(),
                extraction_method="deterministic_pain_point",
                reason="Matched explicit pain point language.",
            )
        )
    return insights


def _concise_pain(text: str) -> str:
    stripped = text.strip().rstrip(".")
    if len(stripped) <= 160:
        return stripped[0].upper() + stripped[1:] + "."
    return stripped[:157].rstrip() + "..."
