from __future__ import annotations

import statistics
import time

import pytest
from services.agent_runtime.tests.agent_brain_helpers import (
    DEMO_SESSION_ID,
    ORG_ID,
    PRODUCT_ID,
    TRANSCRIPT_ID,
    TURN_ID,
    safe_action,
    screen_context,
)
from services.agent_runtime.tests.helpers import test_settings

from live_demo_agent_runtime.context.context_packager import render_context_json
from live_demo_agent_runtime.context.context_types import (
    BuildRealtimeContextRequest,
    KnowledgeFactContext,
    PersonaContext,
    ProductSummaryContext,
    RealtimeAgentContext,
    RecentTurnContext,
    RecipeStepContext,
    SafeActionContext,
)
from live_demo_agent_runtime.context.realtime_context_builder import (
    InMemoryRealtimeContextDataSource,
    RealtimeContextBuilder,
)


@pytest.mark.asyncio
async def test_context_includes_required_grounded_sections() -> None:
    context = await _build_context()

    assert context.current_screen is not None
    assert context.safe_actions
    assert context.active_recipe_step is not None
    assert context.recent_turns
    assert context.persona.likely_role == "founder"
    assert context.product_summary is not None
    assert context.safety_rules.no_raw_js is True
    assert context.source_map
    assert context.token_budget_report.max_tokens == 3000
    assert all(source.source_id and source.source_type for source in context.source_map)
    assert all(0 <= source.confidence <= 1 for source in context.source_map)


@pytest.mark.asyncio
async def test_context_excludes_forbidden_prompt_content() -> None:
    context = await _build_context(
        screen_summary="<html>document.cookie localStorage sessionStorage data:image/png;base64",
        product_summary="API keys and raw provider responses must not appear.",
    )
    rendered = render_context_json(context).lower()

    for forbidden in [
        "<html",
        "document.cookie",
        "localstorage",
        "sessionstorage",
        "data:image",
        "base64",
        "raw provider response",
    ]:
        assert forbidden not in rendered


@pytest.mark.asyncio
async def test_context_token_budget_drops_low_priority_sections_first() -> None:
    context = await _build_context(
        max_tokens=700,
        product_summary="Product summary. " * 1000,
        knowledge=tuple(
            KnowledgeFactContext(f"fact_{index}", "Retrieved fact. " * 120, 0.99, "fixture")
            for index in range(20)
        ),
        recent_turns=tuple(
            RecentTurnContext(
                speaker="user",
                text=f"Turn {index} " * 100,
                chunk_type="final",
                created_at=None,
                turn_id=TURN_ID,
                transcript_event_id=TRANSCRIPT_ID,
            )
            for index in range(30)
        ),
    )

    assert context.token_budget_report.estimated_tokens <= 700
    assert context.current_screen is not None
    assert context.safe_actions
    assert "retrieved_knowledge" in context.token_budget_report.dropped_sections


@pytest.mark.asyncio
async def test_context_handles_retrieval_timeout_without_failing_turn() -> None:
    builder = RealtimeContextBuilder(
        settings=test_settings(agent_knowledge_retrieval_only_on_demand=False),
        data_source=TimeoutDataSource(screen=screen_context()),
    )

    context = await builder.build_context(_request("Can it export reports?"))

    assert context.retrieved_knowledge == ()
    assert "retrieval_unavailable" in context.token_budget_report.dropped_sections


@pytest.mark.asyncio
async def test_context_caps_safe_actions_recent_turns_and_redacts_prompt_text() -> None:
    context = await _build_context(
        screen_summary="Dashboard for alice@example.com with Bearer abcdefghijklmnop1234",
        safe_actions=tuple(safe_action(f"act_{index}") for index in range(100)),
        recent_turns=tuple(
            RecentTurnContext(
                speaker="user",
                text=f"Question {index} from alice@example.com?",
                chunk_type="final",
                created_at=None,
                turn_id=TURN_ID,
                transcript_event_id=TRANSCRIPT_ID,
            )
            for index in range(100)
        ),
    )
    rendered = render_context_json(context)

    assert len(context.safe_actions) == 8
    assert len(context.recent_turns) == 8
    assert "alice@example.com" not in rendered
    assert "Bearer abcdefghijklmnop1234" not in rendered
    assert "[REDACTED_EMAIL]" in rendered
    assert "[REDACTED_BEARER_TOKEN]" in rendered


@pytest.mark.asyncio
async def test_context_builder_p50_under_fifty_ms_for_fixture_inputs() -> None:
    durations: list[float] = []
    for _ in range(40):
        started = time.perf_counter_ns()
        await _build_context()
        durations.append((time.perf_counter_ns() - started) / 1_000_000)

    assert statistics.median(durations) <= 50


class TimeoutDataSource(InMemoryRealtimeContextDataSource):
    async def search_knowledge(
        self,
        request: BuildRealtimeContextRequest,
        top_k: int,
    ) -> list[KnowledgeFactContext]:
        del request, top_k
        raise TimeoutError("fixture retrieval timeout")


async def _build_context(
    *,
    max_tokens: int = 3000,
    screen_summary: str = "Dashboard with revenue metrics and reports.",
    product_summary: str = "MetricFlow shows dashboard metrics.",
    safe_actions: tuple[SafeActionContext, ...] | None = None,
    recent_turns: tuple[RecentTurnContext, ...] = (
        RecentTurnContext(
            speaker="user",
            text="I care about weekly metrics.",
            chunk_type="final",
            created_at=None,
            turn_id=TURN_ID,
            transcript_event_id=TRANSCRIPT_ID,
        ),
    ),
    knowledge: tuple[KnowledgeFactContext, ...] = (
        KnowledgeFactContext("fact_dashboard", "Dashboard includes metric cards.", 0.9, "fixture"),
    ),
) -> RealtimeAgentContext:
    if safe_actions is None:
        safe_actions = tuple(safe_action(f"act_{index}") for index in range(4))
    builder = RealtimeContextBuilder(
        settings=test_settings(
            agent_context_max_tokens=max_tokens,
            agent_knowledge_retrieval_only_on_demand=False,
        ),
        data_source=InMemoryRealtimeContextDataSource(
            demo_phase="OVERVIEW",
            screen=screen_context(screen_summary),
            safe_actions=safe_actions,
            recipe_step=RecipeStepContext(step_key="overview", goal="Show dashboard"),
            recent_turns=recent_turns,
            persona=PersonaContext(likely_role="founder", role_confidence=0.8),
            product_summary=ProductSummaryContext(
                product_name="MetricFlow",
                product_url_domain="example.com",
                summary=product_summary,
                confidence=0.9,
                source="fixture",
            ),
            knowledge=knowledge,
        ),
    )
    return await builder.build_context(_request("Can it export reports?"))


def _request(user_utterance: str) -> BuildRealtimeContextRequest:
    return BuildRealtimeContextRequest(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
        product_id=PRODUCT_ID,
        user_utterance=user_utterance,
        user_transcript_event_id=TRANSCRIPT_ID,
        active_turn_id=TURN_ID,
        trace_id="trace",
    )
