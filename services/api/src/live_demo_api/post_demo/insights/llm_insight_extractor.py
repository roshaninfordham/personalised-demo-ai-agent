"""Optional LLM insight extraction hook.

Phase 13 keeps this path conservative: callers may inject schema-valid LLM output in tests or future
provider code, but invalid or unevidenced items are rejected by deterministic validation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from live_demo_api.post_demo.evidence.evidence_index import EvidenceIndex
from live_demo_api.post_demo.evidence.evidence_redaction import redact_prompt_text
from live_demo_api.post_demo.evidence.evidence_types import SessionEvidenceBundle
from live_demo_api.post_demo.insights.insight_types import (
    POST_DEMO_INSIGHT_TYPES,
    ExtractedLeadInsight,
    normalize_content,
)


class LlmInsightExtractor:
    def build_prompt_input(self, bundle: SessionEvidenceBundle, *, max_chars: int) -> str:
        lines: list[str] = []
        for event in bundle.transcript_events:
            if event.chunk_type == "final":
                lines.append(f"{event.transcript_event_id} {event.speaker}: {event.text}")
        return redact_prompt_text("\n".join(lines))[:max_chars]

    def validate_candidates(
        self, candidates: list[dict[str, Any]], index: EvidenceIndex
    ) -> tuple[ExtractedLeadInsight, ...]:
        output: list[ExtractedLeadInsight] = []
        for candidate in candidates:
            insight_type = str(candidate.get("insight_type", ""))
            if insight_type not in POST_DEMO_INSIGHT_TYPES:
                continue
            evidence = candidate.get("evidence")
            if not isinstance(evidence, dict):
                continue
            transcript_ids = _known_ids(
                evidence.get("transcript_event_ids"),
                index.transcript_by_id,
            )
            action_ids = _known_ids(
                evidence.get("browser_action_ids"),
                index.actions_by_id,
            )
            screen_ids = _known_ids(
                evidence.get("screen_ids"),
                index.screens_by_id,
            )
            recipe_ids = _known_ids(
                evidence.get("recipe_step_ids"),
                index.recipe_steps_by_id,
            )
            if not (transcript_ids or action_ids or screen_ids or recipe_ids):
                continue
            content = str(candidate.get("content", "")).strip()
            if not content or len(content) > 1000:
                continue
            confidence = _bounded_float(candidate.get("confidence"), 0.0)
            importance = _bounded_float(candidate.get("importance"), 0.0)
            output.append(
                ExtractedLeadInsight(
                    insight_type=insight_type,
                    content=content,
                    normalized_content=normalize_content(content),
                    confidence=confidence,
                    importance=importance,
                    evidence_transcript_event_ids=transcript_ids,
                    evidence_browser_action_ids=action_ids,
                    evidence_screen_ids=screen_ids,
                    evidence_recipe_step_ids=recipe_ids,
                    extraction_method="llm_validated",
                    reason=str(candidate.get("reason", "LLM candidate with validated evidence.")),
                )
            )
        return tuple(output)


def _uuid_values(value: object) -> tuple[UUID, ...]:
    if not isinstance(value, list):
        return ()
    parsed: list[UUID] = []
    for item in value:
        try:
            parsed.append(UUID(str(item)))
        except ValueError:
            continue
    return tuple(parsed)


def _known_ids(value: object, known: Mapping[UUID, object]) -> tuple[UUID, ...]:
    return tuple(item for item in _uuid_values(value) if item in known)


def _bounded_float(value: object, default: float) -> float:
    if not isinstance(value, int | float | str):
        return default
    try:
        parsed = float(value)
    except ValueError:
        return default
    return max(0.0, min(1.0, parsed))
