from uuid import uuid4

from live_demo_agent_runtime.vad.interruption_state import InterruptionState
from live_demo_agent_runtime.vad.turn_detection import TurnState, TurnStateMachine


def test_interruption_requires_threshold() -> None:
    state = InterruptionState()
    state.start_assistant_turn(turn_id=uuid4(), text="hello world", now_ms=0)
    assert not state.should_interrupt(100, 180)
    assert state.should_interrupt(180, 180)


def test_turn_state_machine_transitions() -> None:
    machine = TurnStateMachine()
    assert machine.transition_to(TurnState.user_speaking) == TurnState.user_speaking
    assert machine.transition_to(TurnState.possible_user_done) == TurnState.possible_user_done
    assert machine.transition_to(TurnState.user_done) == TurnState.user_done
