"""VAD configuration objects."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VadConfig:
    provider: str
    confidence: float
    max_silence_ms: int
    enable_smart_turn: bool
    interruption_min_user_speech_ms: int
