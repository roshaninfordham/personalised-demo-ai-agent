from __future__ import annotations

from uuid import uuid4

from live_demo_backend_common.policy.redaction import RedactionEngine
from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunkInput
from live_demo_learner_worker.knowledge.knowledge_chunker import KnowledgeChunker


def test_chunks_and_redacts_before_chunking() -> None:
    product_id = uuid4()
    chunks = KnowledgeChunker(
        RedactionEngine(), max_chars=80, overlap_chars=10, min_chars=20
    ).chunk(
        KnowledgeChunkInput(
            organization_id=uuid4(),
            product_id=product_id,
            source_type="screen_summary",
            source_id="screen",
            source_uri=None,
            title="Title",
            content="Contact alice@example.com. Reports can export CSV. " * 5,
            metadata={},
            confidence=0.8,
        )
    )

    assert chunks
    assert "[REDACTED_EMAIL]" in chunks[0].content
    assert chunks[0].content_hash
