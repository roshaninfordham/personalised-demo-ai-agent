"""Optional local Whisper STT adapter skeleton."""

import importlib.util
from datetime import UTC, datetime

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.stt.fake import FakeSpeechToTextProvider
from live_demo_agent_runtime.stt.transcript_types import SttOptions, Transcript
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class WhisperLocalSpeechToTextProvider(FakeSpeechToTextProvider):
    provider_name = "whisper_local"

    def __init__(self, settings: AgentRuntimeSettings) -> None:
        super().__init__()
        self.model_name = settings.whisper_local_model

    async def health_check(self) -> ProviderHealth:
        installed = importlib.util.find_spec("whisper") is not None
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="stt",
            model_name=self.model_name,
            status=ProviderStatus.degraded if installed else ProviderStatus.unhealthy,
            checked_at=datetime.now(UTC),
            safe_message=(
                "Whisper package is installed but realtime integration is not enabled in Phase 7."
                if installed
                else "Whisper package is not installed; no model was loaded or downloaded."
            ),
        )

    async def transcribe_file(self, audio_uri: str, options: SttOptions) -> Transcript:
        del audio_uri, options
        raise ProviderCapabilityError(
            self.provider_name,
            "Whisper local transcription is configured but not implemented in this runtime.",
        )
