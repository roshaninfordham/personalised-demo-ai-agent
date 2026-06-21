"""Allowed demo phase transitions."""

from live_demo_agent_runtime.errors import VoiceSessionStateError
from live_demo_agent_runtime.planner.demo_phase import DemoPhase

ALLOWED_TRANSITIONS: dict[DemoPhase, set[DemoPhase]] = {
    DemoPhase.START: {DemoPhase.DISCOVERY, DemoPhase.OVERVIEW, DemoPhase.RECOVERY, DemoPhase.END},
    DemoPhase.DISCOVERY: {
        DemoPhase.OVERVIEW,
        DemoPhase.CORE_WORKFLOW,
        DemoPhase.Q_AND_A,
        DemoPhase.SUMMARY,
        DemoPhase.RECOVERY,
    },
    DemoPhase.OVERVIEW: {
        DemoPhase.CORE_WORKFLOW,
        DemoPhase.DEEP_DIVE,
        DemoPhase.Q_AND_A,
        DemoPhase.SUMMARY,
        DemoPhase.RECOVERY,
    },
    DemoPhase.CORE_WORKFLOW: {
        DemoPhase.DEEP_DIVE,
        DemoPhase.Q_AND_A,
        DemoPhase.SUMMARY,
        DemoPhase.RECOVERY,
    },
    DemoPhase.DEEP_DIVE: {
        DemoPhase.CORE_WORKFLOW,
        DemoPhase.Q_AND_A,
        DemoPhase.SUMMARY,
        DemoPhase.RECOVERY,
    },
    DemoPhase.Q_AND_A: {
        DemoPhase.OVERVIEW,
        DemoPhase.CORE_WORKFLOW,
        DemoPhase.DEEP_DIVE,
        DemoPhase.SUMMARY,
        DemoPhase.RECOVERY,
    },
    DemoPhase.SUMMARY: {DemoPhase.END, DemoPhase.Q_AND_A, DemoPhase.RECOVERY},
    DemoPhase.RECOVERY: {
        DemoPhase.OVERVIEW,
        DemoPhase.CORE_WORKFLOW,
        DemoPhase.Q_AND_A,
        DemoPhase.SUMMARY,
        DemoPhase.END,
    },
    DemoPhase.END: set(),
}


def validate_phase_transition(current: DemoPhase, next_phase: DemoPhase) -> None:
    if next_phase == current:
        return
    if next_phase not in ALLOWED_TRANSITIONS[current]:
        raise VoiceSessionStateError(
            f"Invalid demo phase transition from {current.value} to {next_phase.value}."
        )
