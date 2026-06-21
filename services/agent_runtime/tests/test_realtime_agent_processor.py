import json
from datetime import UTC, datetime

import pytest

from live_demo_agent_runtime.agent_brain.host_agent_runner import HostAgentRunner
from live_demo_agent_runtime.agent_brain.output_validator import AgentOutputValidator
from live_demo_agent_runtime.context.realtime_context_builder import (
    InMemoryRealtimeContextDataSource,
    RealtimeContextBuilder,
)
from live_demo_agent_runtime.events.redis_event_publisher import InMemoryEventPublisher
from live_demo_agent_runtime.memory.lead_insight_repository import InMemoryLeadInsightRepository
from live_demo_agent_runtime.memory.memory_update_handler import MemoryUpdateHandler
from live_demo_agent_runtime.persona.persona_tracker import PersonaTracker
from live_demo_agent_runtime.pipeline.processors.realtime_agent_processor import (
    RealtimeAgentProcessor,
)
from live_demo_agent_runtime.tools.browser_tool_client import FakeBrowserToolClient
from live_demo_agent_runtime.tools.browser_tool_router import BrowserToolRouter
from live_demo_agent_runtime.transcripts.transcript_buffer import TranscriptWriteItem
from live_demo_backend_common.ai.text.fake import FakeTextProvider

from .agent_brain_helpers import (
    DEMO_SESSION_ID,
    ORG_ID,
    PRODUCT_ID,
    TRANSCRIPT_ID,
    TURN_ID,
    safe_action,
    screen_context,
)
from .helpers import test_settings


def _runner() -> tuple[HostAgentRunner, FakeBrowserToolClient, InMemoryLeadInsightRepository]:
    settings = test_settings()
    publisher = InMemoryEventPublisher()
    repository = InMemoryLeadInsightRepository()
    browser_client = FakeBrowserToolClient()
    runner = HostAgentRunner(
        settings=settings,
        context_builder=RealtimeContextBuilder(
            settings=settings,
            data_source=InMemoryRealtimeContextDataSource(
                screen=screen_context(),
                safe_actions=(safe_action(),),
            ),
        ),
        text_provider=FakeTextProvider(),
        output_validator=AgentOutputValidator(),
        persona_tracker=PersonaTracker(settings),
        memory_handler=MemoryUpdateHandler(
            settings=settings,
            repository=repository,
            event_publisher=publisher,
        ),
        tool_router=BrowserToolRouter(browser_client=browser_client),
        event_publisher=publisher,
    )
    return runner, browser_client, repository


@pytest.mark.asyncio
async def test_final_transcript_triggers_agent_turn_action_and_memory() -> None:
    runner, browser_client, repository = _runner()
    processor = RealtimeAgentProcessor(runner)
    response = json.dumps(
        {
            "spoken_response": "From what I can verify on screen, this is the dashboard.",
            "browser_action": {
                "action_id": "act_click_dashboard",
                "tool_name": "click_element",
                "reason": "The safe action list contains the dashboard action.",
            },
            "memory_updates": [
                {
                    "type": "feature_interest",
                    "content": "User is interested in revenue dashboards.",
                    "confidence": 0.8,
                    "importance": 0.8,
                    "evidence": {
                        "transcript_event_ids": [str(TRANSCRIPT_ID)],
                        "screen_ids": ["screen_dashboard"],
                        "action_ids": [],
                    },
                }
            ],
            "confidence": 0.86,
        }
    )
    result = await processor.process_transcript(
        TranscriptWriteItem(
            transcript_event_id=TRANSCRIPT_ID,
            organization_id=ORG_ID,
            demo_session_id=DEMO_SESSION_ID,
            speaker="user",
            chunk_type="final",
            text="Can you show me the dashboard?",
            is_final=True,
            start_ms=None,
            end_ms=None,
            confidence=0.9,
            turn_id=TURN_ID,
            created_at=datetime.now(UTC),
            persist=True,
            publish=True,
        ),
        product_id=PRODUCT_ID,
        trace_id="trace",
        fake_llm_response=response,
    )
    assert result is not None
    assert result.decision.browser_action is not None
    assert browser_client.calls
    memories = await repository.list_for_session(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
    )
    assert len(memories) == 1


@pytest.mark.asyncio
async def test_partial_transcript_does_not_trigger_llm() -> None:
    runner, browser_client, _repository = _runner()
    processor = RealtimeAgentProcessor(runner)
    result = await processor.process_transcript(
        TranscriptWriteItem(
            transcript_event_id=TRANSCRIPT_ID,
            organization_id=ORG_ID,
            demo_session_id=DEMO_SESSION_ID,
            speaker="user",
            chunk_type="partial",
            text="Can you",
            is_final=False,
            start_ms=None,
            end_ms=None,
            confidence=None,
            turn_id=TURN_ID,
            created_at=datetime.now(UTC),
            persist=False,
            publish=True,
        ),
        product_id=PRODUCT_ID,
        trace_id="trace",
    )
    assert result is None
    assert browser_client.calls == []
