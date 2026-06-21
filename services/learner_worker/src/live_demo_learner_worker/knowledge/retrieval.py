"""Bounded product knowledge retrieval."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from uuid import UUID

from live_demo_backend_common.ai.embeddings.base import EmbeddingProvider
from live_demo_backend_common.ai.types import EmbeddingRequest
from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunk
from live_demo_learner_worker.knowledge.hybrid_retrieval import hybrid_score
from live_demo_learner_worker.knowledge.lexical_search import lexical_search


@dataclass(frozen=True, slots=True)
class KnowledgeRetrievalRequest:
    organization_id: UUID
    product_id: UUID
    query: str
    top_k: int = 5
    min_score: float = 0.72
    filters: dict[str, str] = field(default_factory=dict)
    use_hybrid: bool = True
    trace_id: str | None = None


@dataclass(frozen=True, slots=True)
class RetrievedKnowledge:
    chunk_id: UUID
    content: str
    source_type: str
    source_id: str | None
    title: str | None
    score: float
    vector_score: float | None
    lexical_score: float | None
    metadata: dict[str, str]
    confidence: float


@dataclass(frozen=True, slots=True)
class KnowledgeRetrievalResult:
    items: tuple[RetrievedKnowledge, ...]


class ProductKnowledgeRetriever:
    def __init__(
        self,
        chunks: tuple[KnowledgeChunk, ...],
        embedding_provider: EmbeddingProvider | None = None,
        *,
        vector_weight: float = 0.70,
        lexical_weight: float = 0.30,
    ) -> None:
        self._chunks = chunks
        self._embedding_provider = embedding_provider
        self._vector_weight = vector_weight
        self._lexical_weight = lexical_weight

    async def retrieve(self, request: KnowledgeRetrievalRequest) -> KnowledgeRetrievalResult:
        chunks = tuple(
            chunk
            for chunk in self._chunks
            if chunk.organization_id == request.organization_id
            and chunk.product_id == request.product_id
            and _matches_filters(chunk, request.filters)
        )
        vector_results = await self._vector_results(chunks, request)
        lexical_results = {
            chunk.content_hash: score
            for chunk, score in lexical_search(chunks, request.query, top_k=request.top_k)
        }
        combined: list[RetrievedKnowledge] = []
        for chunk in chunks:
            vector_score = vector_results.get(chunk.content_hash)
            lexical_score = lexical_results.get(chunk.content_hash)
            score = (
                hybrid_score(
                    vector_score,
                    lexical_score,
                    vector_weight=self._vector_weight,
                    lexical_weight=self._lexical_weight,
                )
                if request.use_hybrid
                else vector_score or lexical_score or 0.0
            )
            if score >= request.min_score:
                combined.append(
                    RetrievedKnowledge(
                        chunk_id=chunk.chunk_id,
                        content=chunk.content,
                        source_type=chunk.source_type,
                        source_id=chunk.source_id,
                        title=chunk.title,
                        score=round(score, 4),
                        vector_score=vector_score,
                        lexical_score=lexical_score,
                        metadata=chunk.metadata,
                        confidence=chunk.confidence,
                    )
                )
        return KnowledgeRetrievalResult(
            items=tuple(
                sorted(
                    combined, key=lambda item: (-item.score, item.source_type, str(item.chunk_id))
                )[: request.top_k]
            )
        )

    async def _vector_results(
        self,
        chunks: tuple[KnowledgeChunk, ...],
        request: KnowledgeRetrievalRequest,
    ) -> dict[str, float]:
        if self._embedding_provider is None:
            return {}
        embedded = [chunk for chunk in chunks if chunk.embedding is not None]
        if not embedded:
            return {}
        dimensions = len(embedded[0].embedding or ())
        response = await self._embedding_provider.embed_texts(
            EmbeddingRequest(texts=[request.query], dimensions=dimensions, normalize=True)
        )
        query = response.vectors[0].vector
        return {
            chunk.content_hash: _cosine(query, list(chunk.embedding or ())) for chunk in embedded
        }


def _matches_filters(chunk: KnowledgeChunk, filters: dict[str, str]) -> bool:
    for key, value in filters.items():
        if key == "source_type" and chunk.source_type != value:
            return False
        if chunk.metadata.get(key) != value:
            return False
    return True


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0 or norm_right == 0:
        return 0.0
    return max(0.0, min(1.0, (dot / (norm_left * norm_right) + 1) / 2))
