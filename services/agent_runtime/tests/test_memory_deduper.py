from live_demo_agent_runtime.memory.memory_deduper import (
    MemoryDeduper,
    jaccard_similarity,
    memory_content_hash,
)
from live_demo_agent_runtime.memory.memory_types import MemoryUpdate, StoredMemory

from .agent_brain_helpers import DEMO_SESSION_ID, ORG_ID, TRANSCRIPT_ID


def test_exact_and_similar_memory_dedupe() -> None:
    update = MemoryUpdate(
        type="feature_interest",
        content="User cares about revenue metrics",
        confidence=0.8,
        importance=0.8,
        evidence_transcript_event_ids=(TRANSCRIPT_ID,),
    )
    stored = StoredMemory(
        memory_id="m1",
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
        update=update,
        content_hash=memory_content_hash(update.type, update.content),
    )
    assert (
        MemoryDeduper(similarity_threshold=0.5, max_candidates=50).find_duplicate(
            update,
            (stored,),
        )
        == stored
    )
    assert jaccard_similarity("revenue metrics", "revenue dashboard metrics") > 0.5
