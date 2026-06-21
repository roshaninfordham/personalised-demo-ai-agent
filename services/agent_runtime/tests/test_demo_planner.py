from live_demo_agent_runtime.planner.demo_phase import DemoPhase
from live_demo_agent_runtime.planner.demo_planner import DemoPlanner, DemoPlannerState
from live_demo_agent_runtime.tools.browser_tool_results import ToolRouteResult

from .agent_brain_helpers import realtime_context


def test_demo_planner_failed_action_moves_to_recovery() -> None:
    result = DemoPlanner().update(
        state=DemoPlannerState(phase=DemoPhase.OVERVIEW),
        user_utterance="continue",
        context=realtime_context(),
        tool_result=ToolRouteResult(
            executed=True,
            tool_name="click_element",
            action_id="act",
            success=False,
            policy_decision="allowed",
            risk_level="low",
            browser_action_result=None,
            error_code="browser_action_failed",
            error_message="failed",
            latency_ms=1,
        ),
    )
    assert result.phase == DemoPhase.RECOVERY


def test_demo_planner_question_and_stop_are_deterministic() -> None:
    planner = DemoPlanner()
    qna = planner.update(
        state=DemoPlannerState(phase=DemoPhase.OVERVIEW),
        user_utterance="What about metrics?",
        context=realtime_context(),
    )
    assert qna.phase == DemoPhase.Q_AND_A
    summary = planner.update(
        state=DemoPlannerState(phase=DemoPhase.Q_AND_A),
        user_utterance="thanks",
        context=realtime_context(),
    )
    assert summary.phase == DemoPhase.SUMMARY
