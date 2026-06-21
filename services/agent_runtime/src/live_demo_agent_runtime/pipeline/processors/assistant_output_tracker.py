"""Track assistant spoken output before committing transcripts."""

from uuid import UUID

from live_demo_agent_runtime.tts.audio_types import SynthesizedAudioChunk
from live_demo_agent_runtime.vad.interruption_state import InterruptionState


class AssistantOutputTracker:
    def __init__(self, state: InterruptionState) -> None:
        self._state = state
        self.emitted_audio_duration_ms = 0

    def start_turn(self, *, turn_id: UUID, text: str, now_ms: int) -> None:
        self._state.start_assistant_turn(turn_id=turn_id, text=text, now_ms=now_ms)

    def mark_audio_chunk(self, chunk: SynthesizedAudioChunk, *, now_ms: int) -> None:
        self._state.mark_audio_chunk_sent(text_end_char=chunk.text_end_char, now_ms=now_ms)
        if chunk.sample_rate > 0 and chunk.channels > 0:
            samples = len(chunk.audio) / 2 / chunk.channels
            self.emitted_audio_duration_ms += int(samples / chunk.sample_rate * 1000)

    def complete(self) -> None:
        self._state.clear()
