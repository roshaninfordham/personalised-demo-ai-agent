"""Speech-to-text provider registry."""

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ConfigurationError
from live_demo_agent_runtime.stt.base import SpeechToTextProvider
from live_demo_agent_runtime.stt.custom import CustomSpeechToTextProvider
from live_demo_agent_runtime.stt.deepgram import DeepgramSpeechToTextProvider
from live_demo_agent_runtime.stt.fake import FakeSpeechToTextProvider
from live_demo_agent_runtime.stt.whisper_cpp import WhisperCppSpeechToTextProvider
from live_demo_agent_runtime.stt.whisper_local import WhisperLocalSpeechToTextProvider


class SttProviderRegistry:
    def __init__(self, settings: AgentRuntimeSettings) -> None:
        self._settings = settings
        self._provider: SpeechToTextProvider | None = None

    def get_provider(self) -> SpeechToTextProvider:
        if self._provider is not None:
            return self._provider
        provider_name = self._settings.ai_stt_provider
        if provider_name == "fake":
            self._provider = FakeSpeechToTextProvider()
        elif provider_name == "whisper_local":
            self._provider = WhisperLocalSpeechToTextProvider(self._settings)
        elif provider_name == "whisper_cpp":
            self._provider = WhisperCppSpeechToTextProvider(self._settings)
        elif provider_name == "deepgram":
            self._provider = DeepgramSpeechToTextProvider(self._settings)
        elif provider_name == "custom":
            self._provider = CustomSpeechToTextProvider(self._settings)
        else:
            raise ConfigurationError(f"Unsupported STT provider: {provider_name}")
        return self._provider

    async def close(self) -> None:
        if self._provider is not None:
            await self._provider.close()
