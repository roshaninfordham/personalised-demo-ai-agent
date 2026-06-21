import pytest

from live_demo_agent_runtime.errors import VoiceSessionStateError
from live_demo_agent_runtime.planner.demo_phase import DemoPhase
from live_demo_agent_runtime.planner.phase_transitions import (
    ALLOWED_TRANSITIONS,
    validate_phase_transition,
)


def test_all_allowed_transitions_pass() -> None:
    for current, next_phases in ALLOWED_TRANSITIONS.items():
        for next_phase in next_phases:
            validate_phase_transition(current, next_phase)


def test_invalid_transition_rejected() -> None:
    with pytest.raises(VoiceSessionStateError):
        validate_phase_transition(DemoPhase.END, DemoPhase.START)
