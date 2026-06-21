"""Knowledge chunk deduplication."""

from __future__ import annotations

from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunk


class ChunkDeduper:
    def dedupe(self, chunks: tuple[KnowledgeChunk, ...]) -> tuple[KnowledgeChunk, ...]:
        seen: set[str] = set()
        output: list[KnowledgeChunk] = []
        for chunk in sorted(chunks, key=lambda item: (item.content_hash, item.chunk_id)):
            if chunk.content_hash in seen:
                continue
            if any(
                _jaccard(_shingles(chunk.content), _shingles(existing.content)) >= 0.90
                for existing in output[:100]
            ):
                continue
            seen.add(chunk.content_hash)
            output.append(chunk)
        return tuple(output)


def _shingles(content: str) -> set[tuple[str, str, str]]:
    tokens = content.lower().split()
    return {
        (tokens[index], tokens[index + 1], tokens[index + 2])
        for index in range(max(0, len(tokens) - 2))
    }


def _jaccard(left: set[tuple[str, str, str]], right: set[tuple[str, str, str]]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0
