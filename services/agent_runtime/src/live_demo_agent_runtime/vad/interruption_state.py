"""Assistant interruption state and threshold logic."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class InterruptionState:
    assistant_speaking: bool = False
    current_assistant_turn_id: UUID | None = None
    current_text: str = ""
    spoken_char_count_estimate: int = 0
    tts_started_at_ms: int | None = None
    last_audio_chunk_sent_at_ms: int | None = None
    interrupted_at_ms: int | None = None
    pending_tts_chunks: int = 0

    def start_assistant_turn(self, *, turn_id: UUID, text: str, now_ms: int) -> None:
        self.assistant_speaking = True
        self.current_assistant_turn_id = turn_id
        self.current_text = text
        self.spoken_char_count_estimate = 0
        self.tts_started_at_ms = now_ms
        self.last_audio_chunk_sent_at_ms = None
        self.interrupted_at_ms = None

    def mark_audio_chunk_sent(self, *, text_end_char: int | None, now_ms: int) -> None:
        self.last_audio_chunk_sent_at_ms = now_ms
        if text_end_char is not None:
            self.spoken_char_count_estimate = max(self.spoken_char_count_estimate, text_end_char)

    def should_interrupt(self, user_speech_duration_ms: int, threshold_ms: int) -> bool:
        return self.assistant_speaking and user_speech_duration_ms >= threshold_ms

    def interrupt(self, *, now_ms: int) -> None:
        self.interrupted_at_ms = now_ms
        self.assistant_speaking = False
        self.pending_tts_chunks = 0

    def clear(self) -> None:
        self.assistant_speaking = False
        self.current_assistant_turn_id = None
        self.current_text = ""
        self.spoken_char_count_estimate = 0
        self.tts_started_at_ms = None
        self.last_audio_chunk_sent_at_ms = None
        self.interrupted_at_ms = None
        self.pending_tts_chunks = 0
