from live_demo_agent_runtime.metrics.latency import VoiceLatencyTracker, duration_ms


def test_monotonic_duration_math() -> None:
    assert duration_ms(1_000_000, 3_500_000) == 2.5


def test_latency_snapshot() -> None:
    tracker = VoiceLatencyTracker()
    tracker.mark("assistant_response_created", 1_000_000)
    tracker.mark("tts_first_audio", 21_000_000)
    assert tracker.snapshot()["tts_first_audio_latency_ms"] == 20.0
