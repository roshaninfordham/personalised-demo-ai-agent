from live_demo_agent_runtime.errors import VoiceSessionStateError
from live_demo_agent_runtime.sessions.session_state import VoiceSessionStatus, validate_transition


def test_valid_transition_allowed() -> None:
    validate_transition(VoiceSessionStatus.CREATED, VoiceSessionStatus.STARTING)


def test_invalid_transition_rejected() -> None:
    try:
        validate_transition(VoiceSessionStatus.CREATED, VoiceSessionStatus.ACTIVE)
    except VoiceSessionStateError:
        return
    raise AssertionError("invalid transition was accepted")
