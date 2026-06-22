from services.agent_runtime.tests.helpers import test_settings

from live_demo_agent_runtime.persona.persona_tracker import PersonaTracker


def test_persona_tracker_extracts_founder_metrics_interest() -> None:
    tracker = PersonaTracker(test_settings())
    state = tracker.initial_state()

    state = tracker.update(state, "I'm a founder and I care about weekly metrics.")

    assert state.likely_role == "founder"
    assert any(signal.label == "metrics" for signal in state.interests)
