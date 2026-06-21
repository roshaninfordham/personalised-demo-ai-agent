"""Provider-agnostic text-to-speech interface."""

from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from live_demo_agent_runtime.tts.audio_types import (
    SynthesizedAudio,
    SynthesizedAudioChunk,
    TtsRequest,
)
from live_demo_backend_common.ai.types import ProviderHealth


class TextToSpeechProvider(Protocol):
    provider_name: str
    model_name: str | None
    supports_streaming: bool
    sample_rate: int

    async def health_check(self) -> ProviderHealth: ...

    def synthesize_stream(
        self,
        request: TtsRequest,
    ) -> AsyncIterator[SynthesizedAudioChunk]: ...

    async def synthesize_text(self, request: TtsRequest) -> SynthesizedAudio: ...

    async def stop(self, voice_session_id: UUID) -> None: ...

    async def close(self) -> None: ...
