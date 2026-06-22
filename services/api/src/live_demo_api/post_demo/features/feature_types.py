"""Feature-shown datatypes."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class FeatureCandidate:
    feature_key: str
    feature_label: str
    feature_category: str | None
    confidence: float
    source_type: str
    evidence_transcript_event_ids: tuple[UUID, ...]
    evidence_browser_action_ids: tuple[UUID, ...]
    evidence_screen_ids: tuple[UUID, ...]
    evidence_recipe_step_ids: tuple[UUID, ...]


def feature_key(label: str) -> str:
    text = unicodedata.normalize("NFKC", label).lower()
    text = re.sub(r"[^a-z0-9\s_]+", " ", text)
    text = re.sub(r"\s+", "_", text).strip("_")
    text = re.sub(r"_+", "_", text)
    return text[:80] or "unknown"
