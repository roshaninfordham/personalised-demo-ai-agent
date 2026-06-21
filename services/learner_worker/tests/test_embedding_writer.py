from __future__ import annotations

from uuid import uuid4

import pytest

from live_demo_backend_common.ai.embeddings.fake import FakeEmbeddingProvider
from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunkInput, make_chunk
from live_demo_learner_worker.knowledge.embedding_writer import EmbeddingWriter


@pytest.mark.asyncio
async def test_embedding_writer_stores_vectors() -> None:
    input_data = KnowledgeChunkInput(
        uuid4(), uuid4(), "summary", "1", None, None, "content", {}, 0.8
    )
    chunk = make_chunk(input_data, content="content", redaction_applied=False)

    embedded = await EmbeddingWriter(
        FakeEmbeddingProvider(dimensions=8), dimensions=8
    ).embed_chunks((chunk,))

    assert embedded[0].embedding is not None
    assert len(embedded[0].embedding) == 8
