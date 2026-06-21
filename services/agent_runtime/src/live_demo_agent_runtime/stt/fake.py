"""Deterministic fake STT provider for CI and local no-cost mode."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from live_demo_agent_runtime.stt.transcript_types import (
    AudioFrame,
    SttOptions,
    Transcript,
    TranscriptChunk,
)
from live_demo_backend_common.ai.types import ProviderHealth, ProviderStatus


class FakeSpeechToTextProvider:
    provider_name: str = "fake"
    model_name: str | None = "fake-stt"
    supports_streaming = True
    supports_partials = True

    def __init__(self, script: str = "hello there|can you show the dashboard?") -> None:
        self._script = [item.strip() for item in script.split("|") if item.strip()]

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="stt",
            model_name=self.model_name,
            status=ProviderStatus.healthy,
            checked_at=datetime.now(UTC),
            safe_message="Fake STT provider is available.",
        )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[AudioFrame],
        options: SttOptions,
    ) -> AsyncIterator[TranscriptChunk]:
        index = 0
        async for frame in audio_stream:
            phrase = (
                frame.metadata.get("fake_transcript") or self._script[index % len(self._script)]
            )
            if options.enable_partials:
                first_word = phrase.split(" ", maxsplit=1)[0]
                yield TranscriptChunk(
                    text=first_word,
                    is_final=False,
                    start_ms=frame.timestamp_ms,
                    end_ms=None,
                    confidence=0.99,
                    language=options.language,
                    provider_metadata={"provider": self.provider_name},
                )
            yield TranscriptChunk(
                text=phrase,
                is_final=True,
                start_ms=frame.timestamp_ms,
                end_ms=frame.timestamp_ms + 800,
                confidence=0.99,
                language=options.language,
                provider_metadata={"provider": self.provider_name},
            )
            index += 1
            if frame.is_final:
                break

    async def transcribe_file(self, audio_uri: str, options: SttOptions) -> Transcript:
        del audio_uri
        phrase = self._script[0]
        return Transcript(text=phrase, language=options.language, confidence=0.99)

    async def close(self) -> None:
        return None
