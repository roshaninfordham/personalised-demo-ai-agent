"""O(1) evidence lookup indexes."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from live_demo_api.post_demo.evidence.evidence_types import (
    ActionEvidence,
    RecipeStepEvidence,
    ScreenEvidence,
    SessionEvidenceBundle,
    TranscriptEvidence,
)


@dataclass(frozen=True, slots=True)
class EvidenceIndex:
    transcript_by_id: dict[UUID, TranscriptEvidence]
    actions_by_id: dict[UUID, ActionEvidence]
    screens_by_id: dict[UUID, ScreenEvidence]
    recipe_steps_by_id: dict[UUID, RecipeStepEvidence]
    transcript_by_turn_id: dict[UUID, tuple[TranscriptEvidence, ...]]

    @classmethod
    def build(cls, bundle: SessionEvidenceBundle) -> EvidenceIndex:
        turn_map: dict[UUID, list[TranscriptEvidence]] = {}
        for event in bundle.transcript_events:
            if event.turn_id is not None:
                turn_map.setdefault(event.turn_id, []).append(event)
        return cls(
            transcript_by_id={row.transcript_event_id: row for row in bundle.transcript_events},
            actions_by_id={row.action_event_id: row for row in bundle.action_events},
            screens_by_id={row.screen_id: row for row in bundle.screen_events},
            recipe_steps_by_id={row.recipe_step_progress_id: row for row in bundle.recipe_progress},
            transcript_by_turn_id={key: tuple(value) for key, value in turn_map.items()},
        )
