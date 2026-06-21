"""Bounded allowlist TTS cache."""

from collections import OrderedDict
from hashlib import sha256

from live_demo_agent_runtime.tts.audio_types import SynthesizedAudio

SAFE_TTS_CACHE_PHRASES = {
    "One moment.",
    "Let me show you.",
    "Good question.",
    "I'm opening that now.",
    "Here's what I'm seeing.",
}


class TtsCache:
    def __init__(self, max_items: int = 100, max_audio_bytes: int = 25_000_000) -> None:
        self._max_items = max_items
        self._max_audio_bytes = max_audio_bytes
        self._items: OrderedDict[str, SynthesizedAudio] = OrderedDict()
        self._audio_bytes = 0

    def _key(
        self,
        *,
        provider: str,
        model: str | None,
        voice: str,
        sample_rate: int,
        text: str,
    ) -> str:
        raw = f"{provider}|{model or ''}|{voice}|{sample_rate}|{text}".encode()
        return sha256(raw).hexdigest()

    def get(
        self,
        *,
        provider: str,
        model: str | None,
        voice: str,
        sample_rate: int,
        text: str,
    ) -> SynthesizedAudio | None:
        key = self._key(
            provider=provider,
            model=model,
            voice=voice,
            sample_rate=sample_rate,
            text=text,
        )
        item = self._items.get(key)
        if item is not None:
            self._items.move_to_end(key)
        return item

    def put(
        self,
        *,
        provider: str,
        model: str | None,
        voice: str,
        sample_rate: int,
        text: str,
        audio: SynthesizedAudio,
        cache_allowed: bool,
    ) -> None:
        if not cache_allowed and text not in SAFE_TTS_CACHE_PHRASES:
            return
        key = self._key(
            provider=provider,
            model=model,
            voice=voice,
            sample_rate=sample_rate,
            text=text,
        )
        existing = self._items.pop(key, None)
        if existing is not None:
            self._audio_bytes -= len(existing.audio)
        self._items[key] = audio
        self._audio_bytes += len(audio.audio)
        while len(self._items) > self._max_items or self._audio_bytes > self._max_audio_bytes:
            _, removed = self._items.popitem(last=False)
            self._audio_bytes -= len(removed.audio)

    @property
    def size(self) -> int:
        return len(self._items)
