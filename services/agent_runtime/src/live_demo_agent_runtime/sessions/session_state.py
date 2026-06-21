"""Deterministic voice session states."""

from enum import StrEnum

from live_demo_agent_runtime.errors import VoiceSessionStateError


class VoiceSessionStatus(StrEnum):
    CREATED = "created"
    STARTING = "starting"
    WAITING_FOR_CLIENT = "waiting_for_client"
    CONNECTED = "connected"
    ACTIVE = "active"
    INTERRUPTED = "interrupted"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    EXPIRED = "expired"


ALLOWED_TRANSITIONS: dict[VoiceSessionStatus, frozenset[VoiceSessionStatus]] = {
    VoiceSessionStatus.CREATED: frozenset({VoiceSessionStatus.STARTING, VoiceSessionStatus.FAILED}),
    VoiceSessionStatus.STARTING: frozenset(
        {
            VoiceSessionStatus.WAITING_FOR_CLIENT,
            VoiceSessionStatus.CONNECTED,
            VoiceSessionStatus.FAILED,
            VoiceSessionStatus.STOPPING,
        }
    ),
    VoiceSessionStatus.WAITING_FOR_CLIENT: frozenset(
        {
            VoiceSessionStatus.CONNECTED,
            VoiceSessionStatus.STOPPING,
            VoiceSessionStatus.EXPIRED,
            VoiceSessionStatus.FAILED,
        }
    ),
    VoiceSessionStatus.CONNECTED: frozenset(
        {
            VoiceSessionStatus.ACTIVE,
            VoiceSessionStatus.INTERRUPTED,
            VoiceSessionStatus.STOPPING,
            VoiceSessionStatus.FAILED,
        }
    ),
    VoiceSessionStatus.ACTIVE: frozenset(
        {VoiceSessionStatus.INTERRUPTED, VoiceSessionStatus.STOPPING, VoiceSessionStatus.FAILED}
    ),
    VoiceSessionStatus.INTERRUPTED: frozenset(
        {VoiceSessionStatus.ACTIVE, VoiceSessionStatus.STOPPING, VoiceSessionStatus.FAILED}
    ),
    VoiceSessionStatus.STOPPING: frozenset({VoiceSessionStatus.STOPPED, VoiceSessionStatus.FAILED}),
    VoiceSessionStatus.STOPPED: frozenset(),
    VoiceSessionStatus.FAILED: frozenset(),
    VoiceSessionStatus.EXPIRED: frozenset(),
}


def validate_transition(current: VoiceSessionStatus, next_status: VoiceSessionStatus) -> None:
    if current == next_status:
        return
    if next_status not in ALLOWED_TRANSITIONS[current]:
        msg = f"Invalid voice session transition from {current.value} to {next_status.value}."
        raise VoiceSessionStateError(msg)
