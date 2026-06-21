"""In-memory chunk repository for learner tests and local orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunk


@dataclass(slots=True)
class InMemoryChunkRepository:
    chunks: dict[str, KnowledgeChunk] = field(default_factory=dict)

    async def upsert_chunks(self, chunks: tuple[KnowledgeChunk, ...]) -> tuple[KnowledgeChunk, ...]:
        for chunk in chunks:
            self.chunks[chunk.content_hash] = chunk
        return chunks

    async def list_product_chunks(self, product_id: UUID) -> tuple[KnowledgeChunk, ...]:
        return tuple(chunk for chunk in self.chunks.values() if chunk.product_id == product_id)


@dataclass(slots=True)
class PostgresChunkRepository:
    sessionmaker: async_sessionmaker[AsyncSession]

    async def upsert_chunks(self, chunks: tuple[KnowledgeChunk, ...]) -> tuple[KnowledgeChunk, ...]:
        if not chunks:
            return ()
        async with self.sessionmaker() as session, session.begin():
            for chunk in chunks:
                await session.execute(
                    text(
                        """
                        INSERT INTO knowledge_chunks (
                            chunk_id, organization_id, product_id, source_type, source_id,
                            source_uri, title, content, content_hash, metadata, embedding,
                            search_vector, chunk_type, source_confidence, redaction_applied
                        )
                        VALUES (
                            :chunk_id, :organization_id, :product_id, :source_type,
                            :source_id, :source_uri, :title, :content, :content_hash,
                            CAST(:metadata AS jsonb),
                            CAST(CAST(:embedding AS text) AS vector),
                            to_tsvector('english', :content), :chunk_type,
                            :source_confidence, :redaction_applied
                        )
                        ON CONFLICT ON CONSTRAINT uq_knowledge_chunks_product_id_content_hash
                        DO UPDATE SET
                            source_type = EXCLUDED.source_type,
                            source_id = EXCLUDED.source_id,
                            source_uri = EXCLUDED.source_uri,
                            title = EXCLUDED.title,
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = COALESCE(EXCLUDED.embedding, knowledge_chunks.embedding),
                            search_vector = EXCLUDED.search_vector,
                            chunk_type = EXCLUDED.chunk_type,
                            source_confidence = EXCLUDED.source_confidence,
                            redaction_applied = EXCLUDED.redaction_applied,
                            updated_at = now()
                        """
                    ),
                    {
                        "chunk_id": chunk.chunk_id,
                        "organization_id": chunk.organization_id,
                        "product_id": chunk.product_id,
                        "source_type": chunk.source_type,
                        "source_id": chunk.source_id,
                        "source_uri": chunk.source_uri,
                        "title": chunk.title,
                        "content": chunk.content,
                        "content_hash": chunk.content_hash,
                        "metadata": _json(chunk.metadata),
                        "embedding": _vector_literal(chunk.embedding),
                        "chunk_type": chunk.chunk_type,
                        "source_confidence": chunk.confidence,
                        "redaction_applied": chunk.redaction_applied,
                    },
                )
        return chunks

    async def list_product_chunks(self, product_id: UUID) -> tuple[KnowledgeChunk, ...]:
        async with self.sessionmaker() as session:
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT chunk_id, organization_id, product_id, content, content_hash,
                               chunk_type, source_type, source_id, source_uri, title,
                               metadata, source_confidence, redaction_applied
                        FROM knowledge_chunks
                        WHERE product_id = :product_id AND deleted_at IS NULL
                        ORDER BY created_at ASC, chunk_id ASC
                        LIMIT 100
                        """
                    ),
                    {"product_id": product_id},
                )
            ).mappings().all()
        return tuple(
            KnowledgeChunk(
                chunk_id=row["chunk_id"],
                organization_id=row["organization_id"],
                product_id=row["product_id"],
                content=row["content"],
                content_hash=row["content_hash"],
                chunk_type=row["chunk_type"] or row["source_type"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                source_uri=row["source_uri"],
                title=row["title"],
                metadata=dict(row["metadata"] or {}),
                confidence=float(row["source_confidence"] or 0),
                redaction_applied=bool(row["redaction_applied"]),
            )
            for row in rows
        )


def _json(value: object) -> str:
    import json

    return json.dumps(value, sort_keys=True, default=str)


def _vector_literal(vector: tuple[float, ...] | None) -> str | None:
    if vector is None:
        return None
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"
