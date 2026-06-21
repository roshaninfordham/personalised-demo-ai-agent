"""Optional Cartesia hosted TTS adapter skeleton."""

from datetime import UTC, datetime

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.tts.audio_types import SynthesizedAudio, TtsRequest
from live_demo_agent_runtime.tts.fake import FakeTextToSpeechProvider
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class CartesiaTextToSpeechProvider(FakeTextToSpeechProvider):
    provider_name = "cartesia"

    def __init__(self, settings: AgentRuntimeSettings) -> None:
        super().__init__(settings.ai_tts_sample_rate)
        self.model_name = settings.ai_tts_model
        self._configured = settings.cartesia_api_key is not None

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="tts",
            model_name=self.model_name,
            status=ProviderStatus.degraded if self._configured else ProviderStatus.unhealthy,
            checked_at=datetime.now(UTC),
            safe_message=(
                "Cartesia API key is configured; streaming adapter is not enabled in Phase 7."
                if self._configured
                else "Cartesia API key is not configured."
            ),
        )

    async def synthesize_text(self, request: TtsRequest) -> SynthesizedAudio:
        del request
        raise ProviderCapabilityError(
            self.provider_name,
            "Cartesia synthesis is configured but not implemented in this runtime.",
        )
