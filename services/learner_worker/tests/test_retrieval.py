from __future__ import annotations

from uuid import uuid4

import pytest

from live_demo_backend_common.ai.embeddings.fake import FakeEmbeddingProvider
from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunkInput, make_chunk
from live_demo_learner_worker.knowledge.embedding_writer import EmbeddingWriter
from live_demo_learner_worker.knowledge.retrieval import (
    KnowledgeRetrievalRequest,
    ProductKnowledgeRetriever,
)


@pytest.mark.asyncio
async def test_lexical_and_vector_retrieval_return_top_k() -> None:
    organization_id = uuid4()
    product_id = uuid4()
    chunk = make_chunk(
        KnowledgeChunkInput(
            organization_id,
            product_id,
            "product_summary",
            "1",
            None,
            "Reports",
            "Reports can export CSV files.",
            {},
            0.9,
        ),
        content="Reports can export CSV files.",
        redaction_applied=False,
    )
    provider = FakeEmbeddingProvider(dimensions=8)
    embedded = await EmbeddingWriter(provider, dimensions=8).embed_chunks((chunk,))

    result = await ProductKnowledgeRetriever(embedded, provider).retrieve(
        KnowledgeRetrievalRequest(
            organization_id=organization_id,
            product_id=product_id,
            query="export reports",
            top_k=5,
            min_score=0.0,
        )
    )

    assert len(result.items) == 1
