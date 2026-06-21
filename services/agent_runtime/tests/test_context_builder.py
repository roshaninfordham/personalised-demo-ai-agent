import pytest

from live_demo_agent_runtime.context.context_packager import render_context_json
from live_demo_agent_runtime.context.context_types import (
    BuildRealtimeContextRequest,
    KnowledgeFactContext,
    PersonaContext,
    ProductSummaryContext,
    RecentTurnContext,
    RecipeStepContext,
)
from live_demo_agent_runtime.context.realtime_context_builder import (
    InMemoryRealtimeContextDataSource,
    RealtimeContextBuilder,
)

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


@pytest.mark.asyncio
async def test_context_builder_includes_bounded_grounded_sources() -> None:
    builder = RealtimeContextBuilder(
        settings=test_settings(agent_context_max_safe_actions=1),
        data_source=InMemoryRealtimeContextDataSource(
            demo_phase="OVERVIEW",
            screen=screen_context(),
            safe_actions=(safe_action("b"), safe_action("a")),
            recipe_step=RecipeStepContext(step_key="s1", goal="Show dashboard"),
            recent_turns=tuple(
                RecentTurnContext(
                    speaker="user",
                    text=f"turn {index}",
                    chunk_type="final",
                    created_at=None,
                    turn_id=TURN_ID,
                    transcript_event_id=TRANSCRIPT_ID,
                )
                for index in range(12)
            ),
            persona=PersonaContext(likely_role="founder", role_confidence=0.8),
            product_summary=ProductSummaryContext(
                product_name="Metric Master",
                product_url_domain="example.com",
                summary="Revenue dashboard product.",
                confidence=0.8,
                source="guidance",
            ),
            knowledge=(KnowledgeFactContext("fact1", "Dashboard facts.", 0.9, "test"),),
        ),
    )
    context = await builder.build_context(
        BuildRealtimeContextRequest(
            organization_id=ORG_ID,
            demo_session_id=DEMO_SESSION_ID,
            product_id=PRODUCT_ID,
            user_utterance="Does it support dashboard reporting?",
            user_transcript_event_id=TRANSCRIPT_ID,
            active_turn_id=TURN_ID,
            trace_id="trace",
        )
    )
    assert context.current_screen is not None
    assert len(context.safe_actions) == 1
    assert context.active_recipe_step is not None
    assert len(context.recent_turns) == 8
    assert context.persona.likely_role == "founder"
    assert context.product_summary is not None
    assert context.retrieved_knowledge
    assert context.safety_rules.no_raw_js is True
    assert context.source_map


@pytest.mark.asyncio
async def test_context_builder_excludes_raw_dom_screenshots_and_secrets() -> None:
    builder = RealtimeContextBuilder(
        settings=test_settings(),
        data_source=InMemoryRealtimeContextDataSource(
            screen=screen_context("<html>data:image/png;base64,secret"),
            safe_actions=(safe_action(),),
        ),
    )
    context = await builder.build_context(
        BuildRealtimeContextRequest(
            organization_id=ORG_ID,
            demo_session_id=DEMO_SESSION_ID,
            product_id=PRODUCT_ID,
            user_utterance="show the dashboard",
            user_transcript_event_id=None,
            active_turn_id=TURN_ID,
            trace_id="trace",
        )
    )
    rendered = render_context_json(context).lower()
    assert "<html" not in rendered
    assert "data:image" not in rendered
    assert "base64" not in rendered
    assert "secret" not in rendered


@pytest.mark.asyncio
async def test_context_builder_skips_retrieval_when_not_needed() -> None:
    builder = RealtimeContextBuilder(
        settings=test_settings(),
        data_source=InMemoryRealtimeContextDataSource(
            screen=screen_context(),
            knowledge=(KnowledgeFactContext("fact1", "Salesforce fact", 0.99, "test"),),
        ),
    )
    context = await builder.build_context(
        BuildRealtimeContextRequest(
            organization_id=ORG_ID,
            demo_session_id=DEMO_SESSION_ID,
            product_id=PRODUCT_ID,
            user_utterance="okay continue",
            user_transcript_event_id=None,
            active_turn_id=TURN_ID,
            trace_id="trace",
        )
    )
    assert context.retrieved_knowledge == ()
