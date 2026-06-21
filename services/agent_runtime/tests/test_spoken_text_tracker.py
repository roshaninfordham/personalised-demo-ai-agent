from live_demo_agent_runtime.transcripts.spoken_text_tracker import estimate_spoken_text


def test_alignment_spoken_count_is_preferred() -> None:
    spoken, estimated = estimate_spoken_text(
        text="hello world",
        spoken_char_count=5,
        emitted_audio_duration_ms=1000,
    )
    assert spoken == "hello"
    assert estimated is False


def test_duration_fallback_marks_estimated() -> None:
    spoken, estimated = estimate_spoken_text(
        text="hello world",
        spoken_char_count=None,
        emitted_audio_duration_ms=300,
    )
    assert spoken
    assert estimated is True
