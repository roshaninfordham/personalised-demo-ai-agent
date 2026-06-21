"""Estimate assistant text actually spoken before interruption."""

import math


def estimate_spoken_text(
    *,
    text: str,
    spoken_char_count: int | None,
    emitted_audio_duration_ms: int | None,
    words_per_minute: int = 165,
) -> tuple[str, bool]:
    if spoken_char_count is not None and spoken_char_count > 0:
        return text[: min(spoken_char_count, len(text))], False
    if emitted_audio_duration_ms is None or emitted_audio_duration_ms <= 0:
        return "", True
    word_count = max(1, len(text.split()))
    estimated_total_ms = max(300.0, word_count / words_per_minute * 60_000)
    ratio = max(0.0, min(1.0, emitted_audio_duration_ms / estimated_total_ms))
    char_count = math.floor(len(text) * ratio)
    return text[:char_count], True
