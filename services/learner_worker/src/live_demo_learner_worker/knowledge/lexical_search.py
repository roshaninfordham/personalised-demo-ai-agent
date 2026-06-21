"""Lexical search fallback over in-memory chunks."""

from __future__ import annotations

from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunk


def lexical_search(
    chunks: tuple[KnowledgeChunk, ...], query: str, *, top_k: int
) -> list[tuple[KnowledgeChunk, float]]:
    query_terms = set(query.lower().split())
    scored: list[tuple[KnowledgeChunk, float]] = []
    for chunk in chunks:
        terms = set(chunk.content.lower().split())
        if not terms:
            continue
        score = len(query_terms & terms) / len(query_terms | terms)
        if score > 0:
            scored.append((chunk, score))
    return sorted(scored, key=lambda item: (-item[1], item[0].content_hash))[:top_k]
