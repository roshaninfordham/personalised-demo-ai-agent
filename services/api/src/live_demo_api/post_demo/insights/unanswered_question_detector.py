"""Unanswered question detector."""

from __future__ import annotations

from live_demo_api.post_demo.evidence.evidence_types import (
    SessionEvidenceBundle,
    TranscriptEvidence,
)
from live_demo_api.post_demo.insights.insight_scoring import evidence_strength, score_importance
from live_demo_api.post_demo.insights.insight_types import (
    ExtractedLeadInsight,
    normalize_content,
    token_set,
)

QUESTION_PREFIXES = ("can ", "does ", "do ", "is ", "are ", "how ", "what ", "why ", "when ")
UNCERTAIN_PHRASES = ("cannot verify", "can't verify", "not sure", "i don't know", "uncertain")


def detect_unanswered_questions(bundle: SessionEvidenceBundle) -> list[ExtractedLeadInsight]:
    insights: list[ExtractedLeadInsight] = []
    events = list(bundle.transcript_events)
    for index, event in enumerate(events):
        if event.speaker != "user" or not _is_question(event.text):
            continue
        following = _following_assistant(events, index)
        unanswered = not following or any(
            phrase in normalize_content(answer.text)
            for answer in following
            for phrase in UNCERTAIN_PHRASES
        )
        if not unanswered and following:
            q_tokens = token_set(event.text)
            a_tokens = set().union(*(token_set(answer.text) for answer in following))
            overlap = len(q_tokens & a_tokens) / max(1, len(q_tokens))
            unanswered = overlap < 0.25
        if not unanswered:
            continue
        ids = (event.transcript_event_id,)
        content = event.text.strip().rstrip("?") + "?"
        confidence = 0.7
        importance = score_importance(
            insight_type="unanswered_question",
            confidence=confidence,
            specificity=0.75,
            recency=0.8,
            evidence_strength_value=evidence_strength(transcript_ids=ids),
        )
        insights.append(
            ExtractedLeadInsight(
                insight_type="unanswered_question",
                content=content,
                normalized_content=normalize_content(content),
                confidence=confidence,
                importance=importance,
                evidence_transcript_event_ids=ids,
                evidence_browser_action_ids=(),
                evidence_screen_ids=(),
                evidence_recipe_step_ids=(),
                extraction_method="deterministic_unanswered_question",
                reason="Question had no grounded later answer or assistant expressed uncertainty.",
            )
        )
    return insights


def _is_question(text: str) -> bool:
    normalized = normalize_content(text)
    return text.strip().endswith("?") or normalized.startswith(QUESTION_PREFIXES)


def _following_assistant(events: list[TranscriptEvidence], index: int) -> list[TranscriptEvidence]:
    output: list[TranscriptEvidence] = []
    for event in events[index + 1 :]:
        if event.speaker == "user":
            break
        if event.speaker == "assistant" and event.chunk_type == "final":
            output.append(event)
    return output
