"""Text-to-speech audio data types and deterministic text chunking."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TtsRequest:
    voice_session_id: UUID
    text: str
    voice: str
    sample_rate: int
    interruptible: bool = True
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SynthesizedAudioChunk:
    audio: bytes
    sample_rate: int
    channels: int
    format: str
    is_final: bool
    text_start_char: int | None = None
    text_end_char: int | None = None


@dataclass(frozen=True, slots=True)
class SynthesizedAudio:
    audio: bytes
    sample_rate: int
    channels: int
    format: str
    duration_ms: int


def split_text_for_tts(
    text: str,
    *,
    min_first_chunk_chars: int = 20,
    max_chars: int = 180,
) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks: list[str] = []
    current = []
    current_len = 0
    punctuation = {".", "?", "!", ";", ":", "\n"}
    for char in normalized:
        current.append(char)
        current_len += 1
        should_split = char in punctuation and current_len >= min_first_chunk_chars
        if should_split or current_len >= max_chars:
            chunk = "".join(current).strip()
            if chunk:
                chunks.append(chunk)
            current = []
            current_len = 0
    tail = "".join(current).strip()
    if tail:
        chunks.append(tail)
    if not chunks:
        return [normalized[:max_chars]]
    return chunks
