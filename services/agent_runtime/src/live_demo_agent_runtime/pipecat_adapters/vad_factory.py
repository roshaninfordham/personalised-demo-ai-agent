"""Pipecat VAD adapter boundary."""

import importlib.util

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ConfigurationError
from live_demo_agent_runtime.vad.vad_config import VadConfig


class VadFactory:
    def __init__(self, settings: AgentRuntimeSettings) -> None:
        self._settings = settings

    def build_config(self) -> VadConfig:
        if (
            self._settings.pipecat_vad_provider == "silero"
            and importlib.util.find_spec("pipecat") is None
            and importlib.util.find_spec("pipecat_ai") is None
            and self._settings.ai_stt_provider != "fake"
            and not self._settings.dev_allow_no_vad
        ):
            raise ConfigurationError("Pipecat VAD is unavailable for a non-fake STT provider.")
        return VadConfig(
            provider=self._settings.pipecat_vad_provider,
            confidence=self._settings.pipecat_vad_confidence,
            max_silence_ms=self._settings.pipecat_max_silence_ms,
            enable_smart_turn=self._settings.pipecat_enable_smart_turn,
            interruption_min_user_speech_ms=self._settings.pipecat_interrupt_min_user_speech_ms,
        )
