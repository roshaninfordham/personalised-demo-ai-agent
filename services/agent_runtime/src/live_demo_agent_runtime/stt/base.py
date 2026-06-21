"""Provider-agnostic speech-to-text interface."""

from collections.abc import AsyncIterator
from typing import Protocol

from live_demo_agent_runtime.stt.transcript_types import (
    AudioFrame,
    SttOptions,
    Transcript,
    TranscriptChunk,
)
from live_demo_backend_common.ai.types import ProviderHealth


class SpeechToTextProvider(Protocol):
    provider_name: str
    model_name: str | None
    supports_streaming: bool
    supports_partials: bool

    async def health_check(self) -> ProviderHealth: ...

    def transcribe_stream(
        self,
        audio_stream: AsyncIterator[AudioFrame],
        options: SttOptions,
    ) -> AsyncIterator[TranscriptChunk]: ...

    async def transcribe_file(self, audio_uri: str, options: SttOptions) -> Transcript: ...

    async def close(self) -> None: ...
