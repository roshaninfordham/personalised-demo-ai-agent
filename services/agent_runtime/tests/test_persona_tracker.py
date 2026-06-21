from live_demo_agent_runtime.persona.persona_tracker import PersonaTracker

from .helpers import test_settings


def test_persona_tracker_updates_role_distribution_and_signals() -> None:
    tracker = PersonaTracker(test_settings(persona_min_confidence_to_personalize=0.1))
    state = tracker.initial_state()
    updated = tracker.update(state, "I'm a founder and care about weekly revenue dashboards.")
    assert updated.role_distribution["founder"] > state.role_distribution["founder"]
    assert updated.role_distribution["analytics"] > state.role_distribution["analytics"]
    assert any(signal.label == "dashboard" for signal in updated.interests)
    assert updated.preferred_demo_direction is not None


def test_persona_context_blocks_personalization_below_threshold() -> None:
    tracker = PersonaTracker(test_settings(persona_min_confidence_to_personalize=0.99))
    context = tracker.to_context(tracker.initial_state())
    assert context.likely_role is None
