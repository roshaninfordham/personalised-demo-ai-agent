"""Deterministic turn state machine."""

from enum import StrEnum

from live_demo_agent_runtime.errors import VoiceSessionStateError


class TurnState(StrEnum):
    idle = "idle"
    user_speaking = "user_speaking"
    possible_user_done = "possible_user_done"
    user_done = "user_done"
    assistant_thinking = "assistant_thinking"
    assistant_speaking = "assistant_speaking"
    interrupted = "interrupted"


TURN_TRANSITIONS: dict[TurnState, set[TurnState]] = {
    TurnState.idle: {TurnState.user_speaking},
    TurnState.user_speaking: {TurnState.possible_user_done},
    TurnState.possible_user_done: {TurnState.user_done, TurnState.user_speaking},
    TurnState.user_done: {TurnState.assistant_thinking},
    TurnState.assistant_thinking: {TurnState.assistant_speaking},
    TurnState.assistant_speaking: {TurnState.interrupted, TurnState.idle},
    TurnState.interrupted: {TurnState.user_speaking, TurnState.idle},
}


class TurnStateMachine:
    def __init__(self) -> None:
        self.state = TurnState.idle

    def transition_to(self, next_state: TurnState) -> TurnState:
        if next_state not in TURN_TRANSITIONS[self.state]:
            raise VoiceSessionStateError(
                f"Invalid turn transition from {self.state.value} to {next_state.value}."
            )
        self.state = next_state
        return self.state

    def on_speech_start(
        self,
        *,
        assistant_speaking: bool,
        speech_duration_ms: int = 0,
    ) -> TurnState:
        if assistant_speaking and speech_duration_ms > 0:
            self.state = TurnState.interrupted
            return self.state
        if self.state in {TurnState.idle, TurnState.possible_user_done, TurnState.interrupted}:
            self.state = TurnState.user_speaking
        return self.state

    def on_speech_stop(self) -> TurnState:
        if self.state == TurnState.user_speaking:
            self.state = TurnState.possible_user_done
        return self.state

    def on_turn_complete(self) -> TurnState:
        if self.state == TurnState.possible_user_done:
            self.state = TurnState.user_done
        return self.state
