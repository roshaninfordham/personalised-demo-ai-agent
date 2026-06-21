"""Optional Piper TTS adapter skeleton."""

from datetime import UTC, datetime
from pathlib import Path

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.tts.audio_types import SynthesizedAudio, TtsRequest
from live_demo_agent_runtime.tts.fake import FakeTextToSpeechProvider
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class PiperTextToSpeechProvider(FakeTextToSpeechProvider):
    provider_name = "piper"

    def __init__(self, settings: AgentRuntimeSettings) -> None:
        super().__init__(settings.ai_tts_sample_rate)
        self.model_name = settings.piper_model_path
        self._binary_path = settings.piper_binary_path
        self._model_path = settings.piper_model_path
        self._paths_valid = bool(
            self._binary_path
            and self._model_path
            and Path(self._binary_path).exists()
            and Path(self._model_path).exists()
        )

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="tts",
            model_name=self.model_name,
            status=ProviderStatus.degraded if self._paths_valid else ProviderStatus.unhealthy,
            checked_at=datetime.now(UTC),
            safe_message=(
                "Piper paths are configured; subprocess synthesis is not enabled in Phase 7."
                if self._paths_valid
                else "Piper binary/model paths are missing or invalid."
            ),
        )

    async def synthesize_text(self, request: TtsRequest) -> SynthesizedAudio:
        del request
        raise ProviderCapabilityError(
            self.provider_name,
            "Piper synthesis is configured but not implemented in this runtime.",
        )
