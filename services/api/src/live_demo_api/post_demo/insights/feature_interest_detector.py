"""Feature interest detector."""

from __future__ import annotations

from uuid import UUID

from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.features.feature_evidence_builder import classify_feature
from live_demo_api.post_demo.features.feature_types import feature_key
from live_demo_api.post_demo.insights.insight_scoring import evidence_strength, score_importance
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight, normalize_content

INTEREST_PHRASES = (
    "can",
    "could",
    "show",
    "interested",
    "want",
    "need",
    "how do",
    "how can",
)


def detect_feature_interests(bundle: SessionEvidenceBundle) -> list[ExtractedLeadInsight]:
    evidence_by_category = _feature_evidence_by_category(bundle)
    insights: list[ExtractedLeadInsight] = []
    for event in bundle.transcript_events:
        if event.speaker != "user":
            continue
        normalized = normalize_content(event.text)
        if not any(phrase in normalized for phrase in INTEREST_PHRASES):
            continue
        category, label = classify_feature(event.text)
        if category == "unknown":
            continue
        action_ids, screen_ids = evidence_by_category.get(category, ((), ()))
        ids = (event.transcript_event_id,)
        confidence = 0.70 if (action_ids or screen_ids) else 0.58
        importance = score_importance(
            insight_type="feature_interest",
            confidence=confidence,
            specificity=0.75,
            recency=0.8,
            evidence_strength_value=evidence_strength(
                transcript_ids=ids,
                action_ids=action_ids,
                screen_ids=screen_ids,
            ),
        )
        content = f"User showed interest in {label}."
        insights.append(
            ExtractedLeadInsight(
                insight_type="feature_interest",
                content=content,
                normalized_content=normalize_content(content),
                confidence=confidence,
                importance=importance,
                evidence_transcript_event_ids=ids,
                evidence_browser_action_ids=action_ids,
                evidence_screen_ids=screen_ids,
                evidence_recipe_step_ids=(),
                extraction_method="deterministic_feature_interest",
                reason="User mentioned a feature category with bounded evidence.",
            )
        )
    return insights


def _feature_evidence_by_category(
    bundle: SessionEvidenceBundle,
) -> dict[str, tuple[tuple[UUID, ...], tuple[UUID, ...]]]:
    output: dict[str, tuple[set[UUID], set[UUID]]] = {}
    for action in bundle.action_events:
        raw_label = action.action_payload.get("label") or action.action_payload.get("action_label")
        if raw_label is None:
            continue
        category, _ = classify_feature(str(raw_label))
        if category == "unknown":
            continue
        action_ids, screen_ids = output.setdefault(category, (set(), set()))
        action_ids.add(action.action_event_id)
        for screen_id in (action.from_screen_id, action.to_screen_id):
            if screen_id is not None:
                screen_ids.add(screen_id)
    for screen in bundle.screen_events:
        category, _ = classify_feature(
            " ".join(part for part in (screen.title, screen.summary) if part)
        )
        if category == "unknown":
            continue
        _, screen_ids = output.setdefault(category, (set(), set()))
        screen_ids.add(screen.screen_id)
    return {
        key: (tuple(sorted(action_ids)), tuple(sorted(screen_ids)))
        for key, (action_ids, screen_ids) in output.items()
        if feature_key(key)
    }
