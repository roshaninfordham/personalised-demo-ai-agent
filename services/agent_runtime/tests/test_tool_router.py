from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from live_demo_agent_runtime.agent_brain.agent_decision import AgentDecision
from live_demo_agent_runtime.context.context_types import SafeActionContext
from live_demo_agent_runtime.tools import tool_errors
from live_demo_agent_runtime.tools.browser_tool_client import FakeBrowserToolClient
from live_demo_agent_runtime.tools.browser_tool_results import ToolRouteRequest, ToolRouteResult
from live_demo_agent_runtime.tools.browser_tool_router import BrowserToolRouter

from .agent_brain_helpers import (
    DEMO_SESSION_ID,
    ORG_ID,
    PRODUCT_ID,
    TURN_ID,
    realtime_context,
    safe_action,
)


def _agent_decision(action_id: str | None = "act_click_dashboard") -> AgentDecision:
    return AgentDecision.model_validate(
        {
            "spoken_response": "ok",
            "browser_action": None
            if action_id is None
            else {
                "action_id": action_id,
                "tool_name": "click_element",
                "reason": "Safe action.",
            },
            "memory_updates": [],
            "confidence": 0.8,
        }
    )


async def _route(
    decision: AgentDecision,
    actions: tuple[SafeActionContext, ...] | None = None,
    *,
    fail: bool = False,
) -> ToolRouteResult:
    return await BrowserToolRouter(browser_client=FakeBrowserToolClient(fail=fail)).route(
        ToolRouteRequest(
            organization_id=ORG_ID,
            demo_session_id=DEMO_SESSION_ID,
            product_id=PRODUCT_ID,
            active_turn_id=TURN_ID,
            agent_decision=decision,
            current_context=realtime_context(actions=actions),
            trace_id="trace",
        )
    )


@pytest.mark.asyncio
async def test_null_action_no_execution_and_valid_action_routes() -> None:
    no_action = await _route(_agent_decision(None))
    assert no_action.error_code == tool_errors.NO_ACTION
    routed = await _route(_agent_decision())
    assert routed.executed is True
    assert routed.success is True


@pytest.mark.asyncio
async def test_unknown_expired_blocked_and_high_risk_actions_rejected() -> None:
    assert (await _route(_agent_decision("missing"))).error_code == tool_errors.INVALID_ACTION_ID
    expired = replace(safe_action(), expires_at=datetime.now(UTC) - timedelta(seconds=1))
    assert (await _route(_agent_decision(), (expired,))).error_code == tool_errors.ACTION_EXPIRED
    assert (
        await _route(_agent_decision(), (safe_action(risk_level="blocked"),))
    ).error_code == tool_errors.RISK_BLOCKED
    assert (
        await _route(_agent_decision(), (safe_action(risk_level="high"),))
    ).error_code == tool_errors.CONFIRMATION_REQUIRED


@pytest.mark.asyncio
async def test_duplicate_and_browser_failure_handled() -> None:
    client = FakeBrowserToolClient()
    router = BrowserToolRouter(browser_client=client)
    request = ToolRouteRequest(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
        product_id=PRODUCT_ID,
        active_turn_id=TURN_ID,
        agent_decision=_agent_decision(),
        current_context=realtime_context(),
        trace_id="trace",
    )
    assert (await router.route(request)).success is True
    duplicate = await router.route(request)
    assert duplicate.error_code == tool_errors.DUPLICATE_ACTION_IGNORED
    failed = await _route(_agent_decision(), fail=True)
    assert failed.error_code == tool_errors.BROWSER_ACTION_FAILED
