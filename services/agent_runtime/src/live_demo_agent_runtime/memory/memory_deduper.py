"""Deterministic exact and fuzzy memory deduplication."""

import hashlib
import re

from live_demo_agent_runtime.memory.memory_types import MemoryUpdate, StoredMemory


def canonicalize_memory_content(content: str) -> str:
    return " ".join(content.lower().strip().split())


def memory_content_hash(memory_type: str, content: str) -> str:
    canonical = canonicalize_memory_content(content)
    return hashlib.sha256(f"{memory_type}:{canonical}".encode()).hexdigest()


def jaccard_similarity(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


class MemoryDeduper:
    def __init__(self, *, similarity_threshold: float, max_candidates: int) -> None:
        self._similarity_threshold = similarity_threshold
        self._max_candidates = max_candidates

    def find_duplicate(
        self,
        update: MemoryUpdate,
        existing: tuple[StoredMemory, ...],
    ) -> StoredMemory | None:
        content_hash = memory_content_hash(update.type, update.content)
        same_type = [memory for memory in existing if memory.update.type == update.type]
        for memory in same_type[: self._max_candidates]:
            if memory.content_hash == content_hash:
                return memory
        for memory in same_type[: self._max_candidates]:
            similarity = jaccard_similarity(update.content, memory.update.content)
            if similarity >= self._similarity_threshold:
                return memory
        return None


def merge_memory_update(existing: StoredMemory, new_update: MemoryUpdate) -> MemoryUpdate:
    return MemoryUpdate(
        type=existing.update.type,
        content=existing.update.content,
        confidence=max(existing.update.confidence, new_update.confidence),
        importance=max(existing.update.importance, new_update.importance),
        evidence_transcript_event_ids=_merge_tuple(
            existing.update.evidence_transcript_event_ids,
            new_update.evidence_transcript_event_ids,
            limit=10,
        ),
        evidence_screen_ids=_merge_tuple(
            existing.update.evidence_screen_ids,
            new_update.evidence_screen_ids,
            limit=10,
        ),
        evidence_action_ids=_merge_tuple(
            existing.update.evidence_action_ids,
            new_update.evidence_action_ids,
            limit=10,
        ),
    )


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token}


def _merge_tuple[T](left: tuple[T, ...], right: tuple[T, ...], *, limit: int) -> tuple[T, ...]:
    seen: set[T] = set()
    merged: list[T] = []
    for item in (*left, *right):
        if item in seen:
            continue
        seen.add(item)
        merged.append(item)
        if len(merged) >= limit:
            break
    return tuple(merged)
