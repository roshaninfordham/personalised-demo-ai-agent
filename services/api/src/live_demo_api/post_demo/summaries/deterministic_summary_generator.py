"""Deterministic lead summary generation."""

from __future__ import annotations

from statistics import mean

from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.features.feature_types import FeatureCandidate
from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight
from live_demo_api.post_demo.summaries.summary_schema import empty_summary


class DeterministicSummaryGenerator:
    def generate(
        self,
        *,
        bundle: SessionEvidenceBundle,
        insights: tuple[ExtractedLeadInsight, ...],
        features: tuple[FeatureCandidate, ...],
    ) -> dict[str, object]:
        summary = empty_summary(session_id=bundle.session_id, product_id=bundle.product_id)
        demo_summary = summary["demo_summary"]
        assert isinstance(demo_summary, dict)
        demo_summary["features_shown"] = [
            {
                "feature_key": feature.feature_key,
                "feature_label": feature.feature_label,
                "confidence": feature.confidence,
                "evidence": _feature_evidence(feature),
            }
            for feature in features
        ]
        demo_summary["questions_asked"] = [
            event.text
            for event in bundle.transcript_events
            if event.speaker == "user" and event.text.strip().endswith("?")
        ][:20]
        demo_summary["screens_visited_count"] = len(bundle.screen_events)
        demo_summary["browser_actions_count"] = len(bundle.action_events)
        demo_summary["recipe_steps_completed"] = sum(
            1 for row in bundle.recipe_progress if row.status == "completed"
        )
        demo_summary["recipe_steps_total"] = len(bundle.recipe_progress)

        qualification = summary["qualification"]
        assert isinstance(qualification, dict)
        by_type = _group_insights(insights)
        qualification["pain_points"] = [_insight_payload(item) for item in by_type["pain_point"]]
        qualification["use_cases"] = [_insight_payload(item) for item in by_type["use_case"]]
        qualification["objections"] = [_insight_payload(item) for item in by_type["objection"]]
        qualification["buying_signals"] = [
            _insight_payload(item) for item in by_type["buying_signal"]
        ]
        qualification["feature_interests"] = [
            _insight_payload(item) for item in by_type["feature_interest"]
        ]
        qualification["unanswered_questions"] = [
            _insight_payload(item) for item in by_type["unanswered_question"]
        ]
        urgency = by_type["urgency"][0] if by_type["urgency"] else None
        if urgency is not None:
            qualification["urgency"] = {
                "level": _urgency_level(urgency.confidence),
                "confidence": urgency.confidence,
                "evidence": [str(item) for item in urgency.evidence_transcript_event_ids],
            }
        roles = by_type["role"]
        if roles:
            lead = summary["lead"]
            assert isinstance(lead, dict)
            lead["role"] = {
                "value": _role_value(roles[0].content),
                "confidence": roles[0].confidence,
                "evidence": [str(item) for item in roles[0].evidence_transcript_event_ids],
            }
        qualification["overall_score"] = _overall_score(by_type)
        confidence_values = [item.confidence for item in insights] + [
            item.confidence for item in features
        ]
        qualification["confidence"] = (
            round(mean(confidence_values), 3) if confidence_values else 0.0
        )

        evidence_summary = summary["evidence_summary"]
        assert isinstance(evidence_summary, dict)
        evidence_summary["transcript_event_ids"] = sorted(
            {str(item) for insight in insights for item in insight.evidence_transcript_event_ids}
        )
        evidence_summary["browser_action_ids"] = sorted(
            {str(item) for insight in insights for item in insight.evidence_browser_action_ids}
            | {str(item) for feature in features for item in feature.evidence_browser_action_ids}
        )
        evidence_summary["screen_ids"] = sorted(
            {str(item) for feature in features for item in feature.evidence_screen_ids}
        )
        evidence_summary["recipe_step_ids"] = sorted(
            {str(item) for feature in features for item in feature.evidence_recipe_step_ids}
        )
        return summary


def _group_insights(
    insights: tuple[ExtractedLeadInsight, ...],
) -> dict[str, list[ExtractedLeadInsight]]:
    grouped: dict[str, list[ExtractedLeadInsight]] = {
        "pain_point": [],
        "use_case": [],
        "objection": [],
        "buying_signal": [],
        "urgency": [],
        "feature_interest": [],
        "unanswered_question": [],
        "role": [],
    }
    for insight in insights:
        grouped.setdefault(insight.insight_type, []).append(insight)
    for values in grouped.values():
        values.sort(key=lambda item: (-item.importance, -item.confidence, item.content))
    return grouped


def _insight_payload(insight: ExtractedLeadInsight) -> dict[str, object]:
    return {
        "content": insight.content,
        "confidence": insight.confidence,
        "importance": insight.importance,
        "evidence": {
            "transcript_event_ids": [str(item) for item in insight.evidence_transcript_event_ids],
            "browser_action_ids": [str(item) for item in insight.evidence_browser_action_ids],
            "screen_ids": [str(item) for item in insight.evidence_screen_ids],
            "recipe_step_ids": [str(item) for item in insight.evidence_recipe_step_ids],
        },
    }


def _feature_evidence(feature: FeatureCandidate) -> dict[str, list[str]]:
    return {
        "transcript_event_ids": [str(item) for item in feature.evidence_transcript_event_ids],
        "browser_action_ids": [str(item) for item in feature.evidence_browser_action_ids],
        "screen_ids": [str(item) for item in feature.evidence_screen_ids],
        "recipe_step_ids": [str(item) for item in feature.evidence_recipe_step_ids],
    }


def _urgency_level(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.45:
        return "medium"
    if confidence >= 0.20:
        return "low"
    return "unknown"


def _role_value(content: str) -> str:
    lowered = content.lower()
    for role in (
        "founder",
        "operator",
        "sales",
        "marketing",
        "analytics",
        "engineering",
        "executive",
    ):
        if role in lowered:
            return role
    return "unknown"


def _overall_score(by_type: dict[str, list[ExtractedLeadInsight]]) -> int:
    pain = min(1.0, len(by_type["pain_point"]) / 3)
    buying = min(1.0, len(by_type["buying_signal"]) / 3)
    urgency_value = by_type["urgency"][0].confidence if by_type["urgency"] else 0.0
    feature_interest = min(1.0, len(by_type["feature_interest"]) / 5)
    use_case = min(1.0, len(by_type["use_case"]) / 3)
    objection = min(1.0, len(by_type["objection"]) / 3)
    raw = 100 * (
        0.25 * pain
        + 0.25 * buying
        + 0.20 * urgency_value
        + 0.15 * feature_interest
        + 0.10 * use_case
        - 0.15 * objection
    )
    return round(max(0, min(100, raw)))
