"""Adapter boundary for wrapping TTS providers as Pipecat services."""

from live_demo_agent_runtime.tts.base import TextToSpeechProvider


class TtsServiceAdapter:
    def __init__(self, provider: TextToSpeechProvider) -> None:
        self.provider = provider
