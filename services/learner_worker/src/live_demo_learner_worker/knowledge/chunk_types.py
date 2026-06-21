"""Knowledge chunk types."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class KnowledgeChunkInput:
    organization_id: UUID
    product_id: UUID
    source_type: str
    source_id: str | None
    source_uri: str | None
    title: str | None
    content: str
    metadata: dict[str, str]
    confidence: float


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    chunk_id: UUID
    organization_id: UUID
    product_id: UUID
    content: str
    content_hash: str
    chunk_type: str
    source_type: str
    source_id: str | None
    source_uri: str | None
    title: str | None
    metadata: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    redaction_applied: bool = False
    embedding: tuple[float, ...] | None = None


def content_hash(product_id: UUID, source_type: str, normalized_content: str) -> str:
    return hashlib.sha256(f"{product_id}:{source_type}:{normalized_content}".encode()).hexdigest()


def make_chunk(
    input_data: KnowledgeChunkInput,
    *,
    content: str,
    redaction_applied: bool,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=uuid4(),
        organization_id=input_data.organization_id,
        product_id=input_data.product_id,
        content=content,
        content_hash=content_hash(input_data.product_id, input_data.source_type, content),
        chunk_type=input_data.source_type,
        source_type=input_data.source_type,
        source_id=input_data.source_id,
        source_uri=input_data.source_uri,
        title=input_data.title,
        metadata=input_data.metadata,
        confidence=input_data.confidence,
        redaction_applied=redaction_applied,
    )
