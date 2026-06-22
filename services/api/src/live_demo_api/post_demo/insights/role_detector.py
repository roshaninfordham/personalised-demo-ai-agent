"""Role detector."""

from __future__ import annotations

from live_demo_api.post_demo.evidence.evidence_types import (
    SessionEvidenceBundle,
    TranscriptEvidence,
)
from live_demo_api.post_demo.insights.insight_scoring import evidence_strength, score_importance
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight, normalize_content

ROLE_SIGNALS: dict[str, tuple[str, ...]] = {
    "founder": ("founder", "ceo", "cofounder", "startup", "fundraising", "runway"),
    "operator": ("operations", "ops", "workflow", "process", "team efficiency"),
    "sales": ("sales", "pipeline", "crm", "lead", "deal", "quota"),
    "marketing": ("marketing", "campaign", "attribution", "conversion", "channel"),
    "analytics": ("analytics", "reporting", "dashboard", "kpi", "metrics", "data"),
    "engineering": ("api", "integration", "security", "architecture", "deploy", "sdk"),
    "executive": ("executive", "leadership", "board", "strategy", "roi"),
}


def detect_roles(bundle: SessionEvidenceBundle) -> list[ExtractedLeadInsight]:
    best_role: str | None = None
    best_matches: list[TranscriptEvidence] = []
    best_score = 0.0
    for role, signals in ROLE_SIGNALS.items():
        matches = [
            event
            for event in bundle.transcript_events
            if event.speaker == "user"
            for signal in signals
            if signal in normalize_content(event.text)
        ]
        score = len(matches) / max(1, len(signals))
        if score > best_score:
            best_role = role
            best_matches = matches
            best_score = score
    if best_role is None or not best_matches:
        return []
    evidence_ids = tuple({event.transcript_event_id for event in best_matches})
    explicit = any(
        f"i m a {best_role}" in normalize_content(event.text)
        or f"i am a {best_role}" in normalize_content(event.text)
        or f"as a {best_role}" in normalize_content(event.text)
        for event in best_matches
    )
    confidence = min(1.0, 0.35 + 0.15 * len(evidence_ids) + (0.20 if explicit else 0.0))
    strength = evidence_strength(transcript_ids=evidence_ids)
    importance = score_importance(
        insight_type="role",
        confidence=confidence,
        specificity=0.7,
        recency=0.8,
        evidence_strength_value=strength,
    )
    content = f"User role appears to be {best_role}."
    return [
        ExtractedLeadInsight(
            insight_type="role",
            content=content,
            normalized_content=normalize_content(content),
            confidence=round(confidence, 3),
            importance=importance,
            evidence_transcript_event_ids=evidence_ids,
            evidence_browser_action_ids=(),
            evidence_screen_ids=(),
            evidence_recipe_step_ids=(),
            extraction_method="deterministic_role",
            reason=f"Matched role signals for {best_role}.",
        )
    ]
