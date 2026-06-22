"""Lead insight datatypes."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from uuid import UUID

POST_DEMO_INSIGHT_TYPES = {
    "pain_point",
    "objection",
    "buying_signal",
    "role",
    "urgency",
    "feature_interest",
    "unanswered_question",
    "question",
    "use_case",
    "decision_criteria",
    "next_step",
}


@dataclass(frozen=True, slots=True)
class ExtractedLeadInsight:
    insight_type: str
    content: str
    normalized_content: str
    confidence: float
    importance: float
    evidence_transcript_event_ids: tuple[UUID, ...]
    evidence_browser_action_ids: tuple[UUID, ...]
    evidence_screen_ids: tuple[UUID, ...]
    evidence_recipe_step_ids: tuple[UUID, ...]
    extraction_method: str
    reason: str

    @property
    def normalized_content_hash(self) -> str:
        return normalized_content_hash(
            self.evidence_session_key, self.insight_type, self.normalized_content
        )

    @property
    def evidence_session_key(self) -> str:
        evidence = (
            self.evidence_transcript_event_ids
            or self.evidence_browser_action_ids
            or self.evidence_screen_ids
            or self.evidence_recipe_step_ids
        )
        return str(evidence[0]) if evidence else "no_evidence"


def normalize_content(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalized_content_hash(session_id: object, insight_type: str, normalized_content: str) -> str:
    payload = f"{session_id}:{insight_type}:{normalized_content}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def token_set(value: str) -> set[str]:
    return set(normalize_content(value).split())
