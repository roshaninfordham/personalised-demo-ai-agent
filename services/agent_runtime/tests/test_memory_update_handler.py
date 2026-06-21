import pytest

from live_demo_agent_runtime.events.redis_event_publisher import InMemoryEventPublisher
from live_demo_agent_runtime.memory.lead_insight_repository import InMemoryLeadInsightRepository
from live_demo_agent_runtime.memory.memory_types import MemoryUpdate
from live_demo_agent_runtime.memory.memory_update_handler import MemoryUpdateHandler

from .agent_brain_helpers import DEMO_SESSION_ID, ORG_ID, TRANSCRIPT_ID
from .helpers import test_settings


@pytest.mark.asyncio
async def test_memory_handler_rejects_low_confidence_missing_evidence_and_secrets() -> None:
    publisher = InMemoryEventPublisher()
    handler = MemoryUpdateHandler(
        settings=test_settings(),
        repository=InMemoryLeadInsightRepository(),
        event_publisher=publisher,
    )
    result = await handler.handle_updates(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
        trace_id="trace",
        updates=(
            MemoryUpdate("feature_interest", "Metrics", 0.1, 0.9, (TRANSCRIPT_ID,)),
            MemoryUpdate("feature_interest", "No evidence", 0.9, 0.9),
            MemoryUpdate("feature_interest", "api_key=secret", 0.9, 0.9, (TRANSCRIPT_ID,)),
            MemoryUpdate("feature_interest", "Metrics", 0.9, 0.1, (TRANSCRIPT_ID,)),
        ),
    )
    assert result.accepted == ()
    assert set(result.rejected) == {
        "low_confidence",
        "missing_evidence",
        "secret_like",
        "low_importance",
    }
    assert any(event["event_type"] == "memory.rejected_secret_like" for event in publisher.events)


@pytest.mark.asyncio
async def test_memory_handler_persists_and_merges_duplicates() -> None:
    repository = InMemoryLeadInsightRepository()
    handler = MemoryUpdateHandler(
        settings=test_settings(),
        repository=repository,
        event_publisher=InMemoryEventPublisher(),
    )
    update = MemoryUpdate("feature_interest", "Revenue metrics", 0.9, 0.9, (TRANSCRIPT_ID,))
    first = await handler.handle_updates(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
        trace_id="trace",
        updates=(update,),
    )
    second = await handler.handle_updates(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
        trace_id="trace",
        updates=(update,),
    )
    assert len(first.accepted) == 1
    assert len(second.merged) == 1
    memories = await repository.list_for_session(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
    )
    assert len(memories) == 1
