"""Optional Kokoro TTS adapter skeleton."""

from datetime import UTC, datetime

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.tts.audio_types import SynthesizedAudio, TtsRequest
from live_demo_agent_runtime.tts.fake import FakeTextToSpeechProvider
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class KokoroTextToSpeechProvider(FakeTextToSpeechProvider):
    provider_name = "kokoro"

    def __init__(self, settings: AgentRuntimeSettings) -> None:
        super().__init__(settings.ai_tts_sample_rate)
        self.model_name = settings.ai_tts_model or "kokoro"
        self._base_url = settings.kokoro_base_url

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="tts",
            model_name=self.model_name,
            status=ProviderStatus.degraded if self._base_url else ProviderStatus.unhealthy,
            checked_at=datetime.now(UTC),
            safe_message=(
                "Kokoro service adapter exists; live service call is not enabled in Phase 7."
            ),
        )

    async def synthesize_text(self, request: TtsRequest) -> SynthesizedAudio:
        del request
        raise ProviderCapabilityError(
            self.provider_name,
            "Kokoro synthesis is configured but not implemented in this runtime.",
        )
