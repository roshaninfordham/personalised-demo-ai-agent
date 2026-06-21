"""Turn detection factory boundary for Pipecat version-specific code."""

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.vad.turn_detection import TurnStateMachine


class TurnDetectionFactory:
    def __init__(self, settings: AgentRuntimeSettings) -> None:
        self._settings = settings

    def create_state_machine(self) -> TurnStateMachine:
        return TurnStateMachine()

    @property
    def mode(self) -> str:
        return "smart_turn" if self._settings.pipecat_enable_smart_turn else "basic_vad"
