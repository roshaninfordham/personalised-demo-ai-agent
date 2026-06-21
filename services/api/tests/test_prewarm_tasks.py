from uuid import uuid4

from live_demo_api.orchestration.prewarm_tasks import (
    BrowserPrewarmResult,
    ProviderWarmupResult,
    VoicePrewarmResult,
)


def test_prewarm_task_result_shapes() -> None:
    browser_session_id = uuid4()
    voice_session_id = uuid4()

    browser = BrowserPrewarmResult(
        browser_session_id=browser_session_id,
        screen={"screen_id": "screen_1", "screen_hash": "hash_1"},
        safe_actions=({"action_id": "act_read_current_screen"},),
    )
    voice = VoicePrewarmResult(
        voice_session_id=voice_session_id,
        join_config={"status": "ready_for_signaling"},
    )
    providers = ProviderWarmupResult(warmed_count=2, required_count=3, degraded_reasons=("tts",))

    assert browser.safe_actions[0]["action_id"] == "act_read_current_screen"
    assert voice.join_config["status"] == "ready_for_signaling"
    assert providers.degraded_reasons == ("tts",)
