from datetime import UTC, datetime, timedelta
from uuid import UUID

from live_demo_agent_runtime.context.context_types import (
    ContextBudgetReport,
    KnowledgeFactContext,
    PersonaContext,
    ProductSummaryContext,
    RealtimeAgentContext,
    RecentTurnContext,
    RecipeStepContext,
    SafeActionContext,
    SafetyRulesContext,
    ScreenContext,
)

ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_SESSION_ID = UUID("00000000-0000-0000-0000-000000000010")
PRODUCT_ID = UUID("00000000-0000-0000-0000-000000000020")
TURN_ID = UUID("00000000-0000-0000-0000-000000000030")
TRANSCRIPT_ID = UUID("00000000-0000-0000-0000-000000000040")


def screen_context(summary: str = "Dashboard with weekly revenue metrics.") -> ScreenContext:
    return ScreenContext(
        screen_id="screen_dashboard",
        screen_hash="hash_dashboard",
        url_path="/dashboard",
        title="Dashboard",
        summary=summary,
        confidence=0.9,
        screenshot_artifact_id="artifact_1",
        updated_at=datetime.now(UTC),
    )


def safe_action(
    action_id: str = "act_click_dashboard",
    action_type: str = "click_element",
    risk_level: str = "low",
) -> SafeActionContext:
    return SafeActionContext(
        action_id=action_id,
        action_type=action_type,
        label="Open Dashboard",
        element_id="el_dashboard",
        risk_level=risk_level,
        score=0.9,
        requires_confirmation=risk_level == "high",
        reason="Visible safe dashboard action.",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )


def read_action() -> SafeActionContext:
    return SafeActionContext(
        action_id="act_read_current_screen",
        action_type="read_current_screen",
        label="Read current screen",
        element_id=None,
        risk_level="low",
        score=1.0,
        requires_confirmation=False,
        reason="Refresh screen state.",
    )


def realtime_context(
    *,
    actions: tuple[SafeActionContext, ...] | None = None,
    screen: ScreenContext | None = None,
    product_summary: ProductSummaryContext | None = None,
) -> RealtimeAgentContext:
    return RealtimeAgentContext(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
        product_id=PRODUCT_ID,
        active_turn_id=TURN_ID,
        demo_phase="OVERVIEW",
        user_utterance="Can you show me the dashboard?",
        current_screen=screen or screen_context(),
        safe_actions=actions if actions is not None else (safe_action(), read_action()),
        active_recipe_step=RecipeStepContext(
            step_key="overview",
            goal="Show dashboard",
            talk_track="Explain visible metrics.",
        ),
        recent_turns=(
            RecentTurnContext(
                speaker="user",
                text="I care about revenue metrics.",
                chunk_type="final",
                created_at=datetime.now(UTC),
                turn_id=TURN_ID,
                transcript_event_id=TRANSCRIPT_ID,
            ),
        ),
        persona=PersonaContext(
            likely_role="founder",
            role_confidence=0.8,
            interests=("metrics",),
            evidence=("I care about revenue metrics.",),
        ),
        product_summary=product_summary,
        retrieved_knowledge=(
            KnowledgeFactContext(
                fact_id="fact_dashboard",
                text="The product has a dashboard overview.",
                score=0.9,
                source="test",
            ),
        ),
        safety_rules=SafetyRulesContext(
            never_click=("Delete", "Billing"),
            blocked_actions=("delete",),
            high_risk_requires_confirmation=True,
        ),
        token_budget_report=ContextBudgetReport(max_tokens=3000, estimated_tokens=0),
        source_map=(),
    )
