"""Validate evidence references."""

from __future__ import annotations

from uuid import UUID

from live_demo_api.post_demo.evidence.evidence_index import EvidenceIndex


def has_any_evidence(
    *,
    transcript_ids: tuple[UUID, ...] = (),
    action_ids: tuple[UUID, ...] = (),
    screen_ids: tuple[UUID, ...] = (),
    recipe_step_ids: tuple[UUID, ...] = (),
) -> bool:
    return bool(transcript_ids or action_ids or screen_ids or recipe_step_ids)


def evidence_exists(
    index: EvidenceIndex,
    *,
    transcript_ids: tuple[UUID, ...] = (),
    action_ids: tuple[UUID, ...] = (),
    screen_ids: tuple[UUID, ...] = (),
    recipe_step_ids: tuple[UUID, ...] = (),
) -> bool:
    return (
        all(item in index.transcript_by_id for item in transcript_ids)
        and all(item in index.actions_by_id for item in action_ids)
        and all(item in index.screens_by_id for item in screen_ids)
        and all(item in index.recipe_steps_by_id for item in recipe_step_ids)
        and has_any_evidence(
            transcript_ids=transcript_ids,
            action_ids=action_ids,
            screen_ids=screen_ids,
            recipe_step_ids=recipe_step_ids,
        )
    )
