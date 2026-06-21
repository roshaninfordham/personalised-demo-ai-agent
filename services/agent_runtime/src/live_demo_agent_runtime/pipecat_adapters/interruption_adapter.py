"""Adapter boundary for Pipecat interruption frames."""

from live_demo_agent_runtime.vad.interruption_state import InterruptionState


def should_interrupt_assistant(
    state: InterruptionState,
    *,
    user_speech_duration_ms: int,
    threshold_ms: int,
) -> bool:
    return state.should_interrupt(user_speech_duration_ms, threshold_ms)
