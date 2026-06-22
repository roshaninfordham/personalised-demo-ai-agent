"""Deduplicate feature candidates."""

from __future__ import annotations

from live_demo_api.post_demo.features.feature_scoring import feature_confidence
from live_demo_api.post_demo.features.feature_types import FeatureCandidate


def dedupe_features(candidates: tuple[FeatureCandidate, ...]) -> tuple[FeatureCandidate, ...]:
    by_key: dict[str, FeatureCandidate] = {}
    for candidate in candidates:
        existing = by_key.get(candidate.feature_key)
        if existing is None:
            by_key[candidate.feature_key] = candidate
            continue
        transcript_ids = tuple(
            sorted(
                set(existing.evidence_transcript_event_ids)
                | set(candidate.evidence_transcript_event_ids)
            )
        )
        action_ids = tuple(
            sorted(
                set(existing.evidence_browser_action_ids)
                | set(candidate.evidence_browser_action_ids)
            )
        )
        screen_ids = tuple(
            sorted(set(existing.evidence_screen_ids) | set(candidate.evidence_screen_ids))
        )
        recipe_ids = tuple(
            sorted(set(existing.evidence_recipe_step_ids) | set(candidate.evidence_recipe_step_ids))
        )
        by_key[candidate.feature_key] = FeatureCandidate(
            feature_key=existing.feature_key,
            feature_label=existing.feature_label
            if len(existing.feature_label) >= len(candidate.feature_label)
            else candidate.feature_label,
            feature_category=existing.feature_category or candidate.feature_category,
            confidence=max(
                existing.confidence,
                candidate.confidence,
                feature_confidence(
                    screen_evidence=1.0 if screen_ids else 0.0,
                    action_evidence=1.0 if action_ids else 0.0,
                    recipe_evidence=1.0 if recipe_ids else 0.0,
                    transcript_evidence=1.0 if transcript_ids else 0.0,
                    repeated_evidence=min(
                        1.0,
                        (len(transcript_ids) + len(action_ids) + len(screen_ids) + len(recipe_ids))
                        / 3,
                    ),
                ),
            ),
            source_type=existing.source_type,
            evidence_transcript_event_ids=transcript_ids,
            evidence_browser_action_ids=action_ids,
            evidence_screen_ids=screen_ids,
            evidence_recipe_step_ids=recipe_ids,
        )
    return tuple(
        sorted(
            by_key.values(),
            key=lambda item: (-item.confidence, item.feature_label.lower(), item.feature_key),
        )
    )
