"""Optional Deepgram hosted STT adapter skeleton."""

from datetime import UTC, datetime

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.stt.fake import FakeSpeechToTextProvider
from live_demo_agent_runtime.stt.transcript_types import SttOptions, Transcript
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class DeepgramSpeechToTextProvider(FakeSpeechToTextProvider):
    provider_name = "deepgram"

    def __init__(self, settings: AgentRuntimeSettings) -> None:
        super().__init__()
        self.model_name = settings.deepgram_model
        self._configured = settings.deepgram_api_key is not None

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="stt",
            model_name=self.model_name,
            status=ProviderStatus.degraded if self._configured else ProviderStatus.unhealthy,
            checked_at=datetime.now(UTC),
            safe_message=(
                "Deepgram API key is configured; streaming adapter is not enabled in Phase 7."
                if self._configured
                else "Deepgram API key is not configured."
            ),
        )

    async def transcribe_file(self, audio_uri: str, options: SttOptions) -> Transcript:
        del audio_uri, options
        raise ProviderCapabilityError(
            self.provider_name,
            "Deepgram transcription is configured but not implemented in this runtime.",
        )
