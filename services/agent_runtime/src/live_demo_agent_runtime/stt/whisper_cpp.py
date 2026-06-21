"""Optional whisper.cpp STT adapter skeleton."""

from datetime import UTC, datetime
from pathlib import Path

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.stt.fake import FakeSpeechToTextProvider
from live_demo_agent_runtime.stt.transcript_types import SttOptions, Transcript
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class WhisperCppSpeechToTextProvider(FakeSpeechToTextProvider):
    provider_name = "whisper_cpp"

    def __init__(self, settings: AgentRuntimeSettings) -> None:
        super().__init__()
        self.model_name = settings.whisper_cpp_model_path
        self._binary_path = settings.whisper_cpp_binary_path
        self._model_path = settings.whisper_cpp_model_path
        self._paths_valid = bool(
            self._binary_path
            and self._model_path
            and Path(self._binary_path).exists()
            and Path(self._model_path).exists()
        )

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="stt",
            model_name=self.model_name,
            status=ProviderStatus.degraded if self._paths_valid else ProviderStatus.unhealthy,
            checked_at=datetime.now(UTC),
            safe_message=(
                "whisper.cpp paths are configured; "
                "subprocess integration is not enabled in Phase 7."
                if self._paths_valid
                else "whisper.cpp binary/model paths are missing or invalid."
            ),
        )

    async def transcribe_file(self, audio_uri: str, options: SttOptions) -> Transcript:
        del audio_uri, options
        raise ProviderCapabilityError(
            self.provider_name,
            "whisper.cpp transcription is configured but not implemented in this runtime.",
        )
