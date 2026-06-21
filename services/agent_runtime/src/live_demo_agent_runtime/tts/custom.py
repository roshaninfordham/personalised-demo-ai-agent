"""Custom TTS adapter skeleton."""

from datetime import UTC, datetime

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.tts.audio_types import SynthesizedAudio, TtsRequest
from live_demo_agent_runtime.tts.fake import FakeTextToSpeechProvider
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class CustomTextToSpeechProvider(FakeTextToSpeechProvider):
    provider_name = "custom"

    def __init__(self, settings: AgentRuntimeSettings) -> None:
        super().__init__(settings.ai_tts_sample_rate)
        self.model_name = settings.ai_tts_model
        self._configured = bool(settings.ai_tts_base_url)

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="tts",
            model_name=self.model_name,
            status=ProviderStatus.degraded if self._configured else ProviderStatus.unhealthy,
            checked_at=datetime.now(UTC),
            safe_message=(
                "Custom TTS base URL is configured; adapter is not implemented in Phase 7."
                if self._configured
                else "Custom TTS provider is not configured."
            ),
        )

    async def synthesize_text(self, request: TtsRequest) -> SynthesizedAudio:
        del request
        raise ProviderCapabilityError(
            self.provider_name,
            "Custom TTS synthesis is not implemented in this runtime.",
        )
