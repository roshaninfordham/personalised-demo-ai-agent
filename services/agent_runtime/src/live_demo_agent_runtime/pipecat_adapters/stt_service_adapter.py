"""Adapter boundary for wrapping STT providers as Pipecat services."""

from live_demo_agent_runtime.stt.base import SpeechToTextProvider


class SttServiceAdapter:
    def __init__(self, provider: SpeechToTextProvider) -> None:
        self.provider = provider
