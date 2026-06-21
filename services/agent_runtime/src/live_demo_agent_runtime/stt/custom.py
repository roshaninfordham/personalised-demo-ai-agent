"""Custom STT adapter skeleton."""

from datetime import UTC, datetime

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.stt.fake import FakeSpeechToTextProvider
from live_demo_agent_runtime.stt.transcript_types import SttOptions, Transcript
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class CustomSpeechToTextProvider(FakeSpeechToTextProvider):
    provider_name = "custom"

    def __init__(self, settings: AgentRuntimeSettings) -> None:
        super().__init__()
        self.model_name = settings.ai_stt_model
        self._configured = bool(settings.ai_stt_base_url)

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="stt",
            model_name=self.model_name,
            status=ProviderStatus.degraded if self._configured else ProviderStatus.unhealthy,
            checked_at=datetime.now(UTC),
            safe_message=(
                "Custom STT base URL is configured; adapter is not implemented in Phase 7."
                if self._configured
                else "Custom STT provider is not configured."
            ),
        )

    async def transcribe_file(self, audio_uri: str, options: SttOptions) -> Transcript:
        del audio_uri, options
        raise ProviderCapabilityError(
            self.provider_name,
            "Custom STT transcription is not implemented in this runtime.",
        )
