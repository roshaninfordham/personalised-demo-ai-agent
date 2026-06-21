from uuid import uuid4

from live_demo_agent_runtime.tts.audio_types import (
    SynthesizedAudio,
    TtsRequest,
    split_text_for_tts,
)
from live_demo_agent_runtime.tts.fake import FakeTextToSpeechProvider
from live_demo_agent_runtime.tts.piper import PiperTextToSpeechProvider
from live_demo_agent_runtime.tts.tts_cache import TtsCache
from live_demo_backend_common.ai.types import ProviderStatus

from .helpers import test_settings


async def test_fake_tts_emits_deterministic_audio_chunks() -> None:
    provider = FakeTextToSpeechProvider(sample_rate=24000)
    request = TtsRequest(
        voice_session_id=uuid4(),
        text="Hello there.",
        voice="default",
        sample_rate=24000,
    )
    chunks = [chunk async for chunk in provider.synthesize_stream(request)]
    assert chunks
    assert chunks[0].audio == b"\x00\x00" * int(24000 * max(200, len("Hello there.") * 30) / 1000)


async def test_fake_tts_stop_cancels_future_chunks() -> None:
    provider = FakeTextToSpeechProvider(sample_rate=24000)
    session_id = uuid4()
    await provider.stop(session_id)
    request = TtsRequest(
        voice_session_id=session_id,
        text="Hello there.",
        voice="default",
        sample_rate=24000,
    )
    chunks = [chunk async for chunk in provider.synthesize_stream(request)]
    assert chunks


async def test_piper_missing_paths_unhealthy() -> None:
    provider = PiperTextToSpeechProvider(test_settings())
    health = await provider.health_check()
    assert health.status == ProviderStatus.unhealthy


def test_text_chunker_splits_long_text_deterministically() -> None:
    text = "One sentence. Two sentence. " + ("word " * 80)
    assert split_text_for_tts(text) == split_text_for_tts(text)
    assert all(len(chunk) <= 180 for chunk in split_text_for_tts(text))


def test_tts_cache_allowlist_and_lru() -> None:
    cache = TtsCache(max_items=1, max_audio_bytes=1000)
    audio = SynthesizedAudio(
        audio=b"\x00\x00",
        sample_rate=24000,
        channels=1,
        format="pcm_s16le",
        duration_ms=1,
    )
    cache.put(
        provider="fake",
        model=None,
        voice="default",
        sample_rate=24000,
        text="One moment.",
        audio=audio,
        cache_allowed=False,
    )
    assert cache.size == 1
