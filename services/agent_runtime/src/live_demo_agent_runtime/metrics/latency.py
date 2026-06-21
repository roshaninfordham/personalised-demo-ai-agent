"""Voice latency measurement using monotonic time."""

import time
from dataclasses import dataclass, field


def now_ns() -> int:
    return time.perf_counter_ns()


def duration_ms(start_ns: int, end_ns: int) -> float:
    return (end_ns - start_ns) / 1_000_000


@dataclass(slots=True)
class VoiceLatencyTracker:
    markers: dict[str, int] = field(default_factory=dict)

    def mark(self, name: str, timestamp_ns: int | None = None) -> None:
        self.markers[name] = timestamp_ns if timestamp_ns is not None else now_ns()

    def between(self, start: str, end: str) -> float | None:
        start_ns = self.markers.get(start)
        end_ns = self.markers.get(end)
        if start_ns is None or end_ns is None:
            return None
        return duration_ms(start_ns, end_ns)

    def snapshot(self) -> dict[str, float]:
        values: dict[str, float] = {}
        pairs = {
            "vad_start_latency_ms": ("audio_frame_received", "vad_speech_start"),
            "stt_partial_latency_ms": ("audio_frame_received", "stt_partial"),
            "stt_final_latency_ms": ("audio_frame_received", "stt_final"),
            "turn_end_latency_ms": ("vad_speech_stop", "turn_decided"),
            "tts_first_audio_latency_ms": ("assistant_response_created", "tts_first_audio"),
            "first_audio_after_user_turn_ms": ("turn_decided", "tts_first_audio"),
            "interrupt_stop_latency_ms": ("interruption_detected", "tts_stop_completed"),
        }
        for key, (start, end) in pairs.items():
            value = self.between(start, end)
            if value is not None:
                values[key] = value
        return values
