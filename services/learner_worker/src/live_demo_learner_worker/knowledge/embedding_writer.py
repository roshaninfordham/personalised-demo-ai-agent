"""Embedding writer for redacted knowledge chunks."""

from __future__ import annotations

from dataclasses import replace

from live_demo_backend_common.ai.embeddings.base import EmbeddingProvider
from live_demo_backend_common.ai.types import EmbeddingRequest
from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunk


class EmbeddingWriter:
    def __init__(
        self, provider: EmbeddingProvider, *, dimensions: int = 768, batch_size: int = 32
    ) -> None:
        self._provider = provider
        self._dimensions = dimensions
        self._batch_size = batch_size

    async def embed_chunks(self, chunks: tuple[KnowledgeChunk, ...]) -> tuple[KnowledgeChunk, ...]:
        output: list[KnowledgeChunk] = []
        for index in range(0, len(chunks), self._batch_size):
            batch = chunks[index : index + self._batch_size]
            response = await self._provider.embed_texts(
                EmbeddingRequest(
                    texts=[chunk.content for chunk in batch],
                    dimensions=self._dimensions,
                    normalize=True,
                    metadata={"purpose": "learner_knowledge"},
                )
            )
            vectors_by_index = {vector.text_index: vector for vector in response.vectors}
            for chunk_index, chunk in enumerate(batch):
                vector = vectors_by_index[chunk_index]
                if vector.dimensions != self._dimensions:
                    raise ValueError("Embedding dimension mismatch.")
                output.append(replace(chunk, embedding=tuple(vector.vector)))
        return tuple(output)
