from collections.abc import AsyncIterator

from live_demo_agent_runtime.stt import SttProviderRegistry
from live_demo_agent_runtime.stt.fake import FakeSpeechToTextProvider
from live_demo_agent_runtime.stt.transcript_types import AudioFrame, SttOptions
from live_demo_agent_runtime.stt.whisper_cpp import WhisperCppSpeechToTextProvider
from live_demo_backend_common.ai.types import ProviderStatus

from .helpers import test_settings


async def _frames() -> AsyncIterator[AudioFrame]:
    yield AudioFrame(
        audio=b"\x00\x00",
        sample_rate=16000,
        channels=1,
        sample_width_bytes=2,
        timestamp_ms=0,
        is_final=True,
        metadata={"fake_transcript": "hello test"},
    )


async def test_fake_stt_emits_deterministic_partials_and_finals() -> None:
    provider = FakeSpeechToTextProvider()
    chunks = [chunk async for chunk in provider.transcribe_stream(_frames(), SttOptions())]
    assert [chunk.text for chunk in chunks] == ["hello", "hello test"]
    assert chunks[-1].is_final is True


async def test_whisper_cpp_missing_paths_unhealthy() -> None:
    provider = WhisperCppSpeechToTextProvider(test_settings())
    health = await provider.health_check()
    assert health.status == ProviderStatus.unhealthy


def test_stt_registry_reuses_provider() -> None:
    registry = SttProviderRegistry(test_settings())
    assert registry.get_provider() is registry.get_provider()
