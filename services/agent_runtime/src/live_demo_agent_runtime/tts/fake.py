"""Deterministic fake TTS provider."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

from live_demo_agent_runtime.tts.audio_types import (
    SynthesizedAudio,
    SynthesizedAudioChunk,
    TtsRequest,
    split_text_for_tts,
)
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class FakeTextToSpeechProvider:
    provider_name: str = "fake"
    model_name: str | None = "fake-tts"
    supports_streaming = True

    def __init__(self, sample_rate: int = 24000) -> None:
        self.sample_rate = sample_rate
        self._stopped: set[UUID] = set()

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="tts",
            model_name=self.model_name,
            status=ProviderStatus.healthy,
            checked_at=datetime.now(UTC),
            safe_message="Fake TTS provider is available.",
        )

    async def synthesize_stream(
        self,
        request: TtsRequest,
    ) -> AsyncIterator[SynthesizedAudioChunk]:
        self._stopped.discard(request.voice_session_id)
        offset = 0
        chunks = split_text_for_tts(request.text)
        if not chunks:
            chunks = [""]
        for index, text_chunk in enumerate(chunks):
            if request.voice_session_id in self._stopped:
                break
            duration_ms = max(200, min(1200, len(text_chunk) * 30))
            sample_count = int(request.sample_rate * duration_ms / 1000)
            audio = b"\x00\x00" * sample_count
            end = offset + len(text_chunk)
            yield SynthesizedAudioChunk(
                audio=audio,
                sample_rate=request.sample_rate,
                channels=1,
                format="pcm_s16le",
                is_final=index == len(chunks) - 1,
                text_start_char=offset,
                text_end_char=end,
            )
            offset = end + 1

    async def synthesize_text(self, request: TtsRequest) -> SynthesizedAudio:
        chunks = [chunk async for chunk in self.synthesize_stream(request)]
        audio = b"".join(chunk.audio for chunk in chunks)
        duration_ms = (
            int((len(audio) / 2) / request.sample_rate * 1000) if request.sample_rate else 0
        )
        return SynthesizedAudio(
            audio=audio,
            sample_rate=request.sample_rate,
            channels=1,
            format="pcm_s16le",
            duration_ms=duration_ms,
        )

    async def stop(self, voice_session_id: UUID) -> None:
        self._stopped.add(voice_session_id)

    async def close(self) -> None:
        self._stopped.clear()
