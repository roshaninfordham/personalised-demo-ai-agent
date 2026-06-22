"""Evidence-backed feature shown tracker."""

from __future__ import annotations

from live_demo_api.config import get_settings
from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.features.feature_deduper import dedupe_features
from live_demo_api.post_demo.features.feature_evidence_builder import classify_feature
from live_demo_api.post_demo.features.feature_scoring import feature_confidence
from live_demo_api.post_demo.features.feature_types import FeatureCandidate, feature_key


class FeatureShownTracker:
    def track(self, bundle: SessionEvidenceBundle) -> tuple[FeatureCandidate, ...]:
        settings = get_settings()
        candidates: list[FeatureCandidate] = []
        if settings.feature_tracking_use_recipe_steps:
            candidates.extend(_from_recipe(bundle))
        if settings.feature_tracking_use_screen_summaries:
            candidates.extend(_from_screens(bundle))
        if settings.feature_tracking_use_browser_actions:
            candidates.extend(_from_actions(bundle))
        if settings.feature_tracking_use_transcript_references:
            candidates.extend(_from_transcript(bundle))
        deduped = dedupe_features(tuple(candidates))
        return tuple(
            item
            for item in deduped[: settings.feature_tracking_max_features]
            if item.confidence >= settings.feature_tracking_min_confidence
        )


def _from_recipe(bundle: SessionEvidenceBundle) -> list[FeatureCandidate]:
    output: list[FeatureCandidate] = []
    for step in bundle.recipe_progress:
        if step.status not in {"completed", "adapted"}:
            continue
        label = str(step.evidence.get("goal") or step.step_key.replace("_", " ").title())
        category, fallback_label = classify_feature(label)
        final_label = label if label else fallback_label
        confidence = 0.85 if step.status == "completed" else 0.60
        output.append(
            FeatureCandidate(
                feature_key=feature_key(final_label),
                feature_label=final_label,
                feature_category=category,
                confidence=confidence,
                source_type="recipe_step",
                evidence_transcript_event_ids=(),
                evidence_browser_action_ids=(),
                evidence_screen_ids=(step.matched_screen_id,) if step.matched_screen_id else (),
                evidence_recipe_step_ids=(step.recipe_step_progress_id,),
            )
        )
    return output


def _from_screens(bundle: SessionEvidenceBundle) -> list[FeatureCandidate]:
    output: list[FeatureCandidate] = []
    for screen in bundle.screen_events:
        text = " ".join(part for part in (screen.title, screen.summary) if part)
        if not text:
            continue
        category, label = classify_feature(text)
        output.append(
            FeatureCandidate(
                feature_key=feature_key(label),
                feature_label=label,
                feature_category=category,
                confidence=feature_confidence(
                    screen_evidence=1.0,
                    action_evidence=0.0,
                    recipe_evidence=0.0,
                    transcript_evidence=0.0,
                    repeated_evidence=0.3,
                ),
                source_type="screen_summary",
                evidence_transcript_event_ids=(),
                evidence_browser_action_ids=(),
                evidence_screen_ids=(screen.screen_id,),
                evidence_recipe_step_ids=(),
            )
        )
    return output


def _from_actions(bundle: SessionEvidenceBundle) -> list[FeatureCandidate]:
    output: list[FeatureCandidate] = []
    for action in bundle.action_events:
        if action.success is not True:
            continue
        raw_label = action.action_payload.get("label") or action.action_payload.get("action_label")
        if raw_label is None:
            raw_label = action.action_type.replace("_", " ")
        label_text = str(raw_label)
        category, label = classify_feature(label_text)
        output.append(
            FeatureCandidate(
                feature_key=feature_key(label),
                feature_label=label,
                feature_category=category,
                confidence=feature_confidence(
                    screen_evidence=0.0,
                    action_evidence=1.0,
                    recipe_evidence=0.0,
                    transcript_evidence=0.0,
                    repeated_evidence=0.3,
                ),
                source_type="browser_action",
                evidence_transcript_event_ids=(),
                evidence_browser_action_ids=(action.action_event_id,),
                evidence_screen_ids=tuple(
                    screen_id
                    for screen_id in (action.from_screen_id, action.to_screen_id)
                    if screen_id is not None
                ),
                evidence_recipe_step_ids=(),
            )
        )
    return output


def _from_transcript(bundle: SessionEvidenceBundle) -> list[FeatureCandidate]:
    output: list[FeatureCandidate] = []
    for event in bundle.transcript_events:
        if event.speaker != "assistant":
            continue
        normalized = event.text.lower()
        if "show" not in normalized and "opening" not in normalized:
            continue
        category, label = classify_feature(event.text)
        if category == "unknown":
            continue
        output.append(
            FeatureCandidate(
                feature_key=feature_key(label),
                feature_label=label,
                feature_category=category,
                confidence=feature_confidence(
                    screen_evidence=0.0,
                    action_evidence=0.0,
                    recipe_evidence=0.0,
                    transcript_evidence=1.0,
                    repeated_evidence=0.2,
                ),
                source_type="transcript_reference",
                evidence_transcript_event_ids=(event.transcript_event_id,),
                evidence_browser_action_ids=(),
                evidence_screen_ids=(),
                evidence_recipe_step_ids=(),
            )
        )
    return output
