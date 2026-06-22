from services.agent_runtime.tests.agent_brain_helpers import realtime_context

from live_demo_agent_runtime.planner.demo_phase import DemoPhase
from live_demo_agent_runtime.planner.demo_planner import DemoPlanner, DemoPlannerState


def test_demo_planner_starts_in_configured_phase() -> None:
    next_state = DemoPlanner().update(
        state=DemoPlannerState(phase=DemoPhase.START),
        user_utterance="continue overview",
        context=realtime_context(),
    )

    assert next_state.phase == DemoPhase.OVERVIEW
