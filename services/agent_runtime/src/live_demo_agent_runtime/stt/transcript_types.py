"""Speech-to-text data types used by provider adapters."""

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AudioFrame:
    audio: bytes
    sample_rate: int
    channels: int
    sample_width_bytes: int
    timestamp_ms: int
    is_final: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SttOptions:
    language: str = "en"
    enable_partials: bool = True
    sample_rate: int = 16000
    timeout_ms: int = 10000


@dataclass(frozen=True, slots=True)
class TranscriptChunk:
    text: str
    is_final: bool
    start_ms: int | None
    end_ms: int | None
    confidence: float | None
    language: str | None
    provider_metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Transcript:
    text: str
    language: str | None
    confidence: float | None
    start_ms: int | None = None
    end_ms: int | None = None
