from __future__ import annotations

from uuid import uuid4

from live_demo_learner_worker.knowledge.chunk_deduper import ChunkDeduper
from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunkInput, make_chunk


def test_exact_duplicate_removed() -> None:
    input_data = KnowledgeChunkInput(
        uuid4(), uuid4(), "summary", "1", None, None, "same content", {}, 0.8
    )
    chunk = make_chunk(input_data, content="same content", redaction_applied=False)
    duplicate = make_chunk(input_data, content="same content", redaction_applied=False)

    assert len(ChunkDeduper().dedupe((chunk, duplicate))) == 1
