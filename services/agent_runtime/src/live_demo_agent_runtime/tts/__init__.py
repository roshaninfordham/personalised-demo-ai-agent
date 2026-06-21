"""Text-to-speech provider registry."""

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ConfigurationError
from live_demo_agent_runtime.tts.base import TextToSpeechProvider
from live_demo_agent_runtime.tts.cartesia import CartesiaTextToSpeechProvider
from live_demo_agent_runtime.tts.custom import CustomTextToSpeechProvider
from live_demo_agent_runtime.tts.fake import FakeTextToSpeechProvider
from live_demo_agent_runtime.tts.kokoro import KokoroTextToSpeechProvider
from live_demo_agent_runtime.tts.piper import PiperTextToSpeechProvider


class TtsProviderRegistry:
    def __init__(self, settings: AgentRuntimeSettings) -> None:
        self._settings = settings
        self._provider: TextToSpeechProvider | None = None

    def get_provider(self) -> TextToSpeechProvider:
        if self._provider is not None:
            return self._provider
        provider_name = self._settings.ai_tts_provider
        if provider_name == "fake":
            self._provider = FakeTextToSpeechProvider(self._settings.ai_tts_sample_rate)
        elif provider_name == "kokoro":
            self._provider = KokoroTextToSpeechProvider(self._settings)
        elif provider_name == "piper":
            self._provider = PiperTextToSpeechProvider(self._settings)
        elif provider_name == "cartesia":
            self._provider = CartesiaTextToSpeechProvider(self._settings)
        elif provider_name == "custom":
            self._provider = CustomTextToSpeechProvider(self._settings)
        else:
            raise ConfigurationError(f"Unsupported TTS provider: {provider_name}")
        return self._provider

    async def close(self) -> None:
        if self._provider is not None:
            await self._provider.close()
