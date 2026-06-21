"""Configuration for the internal Pipecat agent runtime service."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TransportProviderName = Literal["small_webrtc", "daily", "custom"]
SttProviderName = Literal["fake", "whisper_local", "whisper_cpp", "deepgram", "custom"]
TtsProviderName = Literal["fake", "kokoro", "piper", "cartesia", "custom"]


class AgentRuntimeSettings(BaseSettings):
    app_env: str = "local"
    app_name: str = "live-demo-agent-runtime"
    log_level: str = "info"

    database_url: str = "postgresql+asyncpg://demo_agent:demo_agent@localhost:5432/demo_agent"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout_seconds: int = 30

    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "live_demo"
    redis_session_ttl_seconds: int = 86400
    redis_event_stream_maxlen: int = 10000

    agent_runtime_host: str = "0.0.0.0"  # noqa: S104 - service bind host is configuration.
    agent_runtime_port: int = 8300
    agent_shutdown_grace_seconds: int = 10
    voice_session_stop_timeout_seconds: int = 5

    transport_provider: TransportProviderName = "small_webrtc"
    transport_room_ttl_seconds: int = 3600
    transport_enable_audio: bool = True
    transport_enable_video: bool = False

    daily_api_key: SecretStr | None = None
    daily_domain: str | None = None
    daily_room_url: str | None = None

    ai_stt_provider: SttProviderName = "fake"
    ai_stt_base_url: str | None = None
    ai_stt_api_key: SecretStr | None = None
    ai_stt_model: str | None = None
    ai_stt_language: str = "en"
    ai_stt_device: str = "cpu"
    ai_stt_enable_partials: bool = True
    ai_stt_sample_rate: int = 16000
    ai_stt_timeout_ms: int = 10000

    whisper_local_model: str = "base"
    whisper_local_device: str = "cpu"
    whisper_local_auto_download: bool = False
    whisper_cpp_binary_path: str | None = None
    whisper_cpp_model_path: str | None = None
    whisper_cpp_worker_mode: str = "utterance"
    deepgram_api_key: SecretStr | None = None
    deepgram_model: str | None = None
    deepgram_language: str = "en"

    ai_tts_provider: TtsProviderName = "fake"
    ai_tts_base_url: str | None = None
    ai_tts_api_key: SecretStr | None = None
    ai_tts_model: str | None = None
    ai_tts_voice: str = "default"
    ai_tts_sample_rate: int = 24000
    ai_tts_enable_streaming: bool = True
    ai_tts_enable_cache: bool = True
    ai_tts_timeout_ms: int = 10000
    ai_tts_cache_max_items: int = 100
    ai_tts_cache_max_audio_bytes: int = 25_000_000

    kokoro_base_url: str = "http://tts:8100"
    kokoro_voice: str = "af_heart"
    piper_binary_path: str | None = None
    piper_model_path: str | None = None
    cartesia_api_key: SecretStr | None = None
    cartesia_voice_id: str | None = None

    pipecat_enable_interruption: bool = True
    pipecat_enable_smart_turn: bool = True
    pipecat_vad_provider: str = "silero"
    pipecat_vad_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    pipecat_max_silence_ms: int = 800
    pipecat_max_agent_monologue_seconds: int = 10
    pipecat_interrupt_min_user_speech_ms: int = 180
    pipecat_interrupt_stop_tts_within_ms: int = 150
    dev_allow_no_vad: bool = False

    transcript_flush_interval_ms: int = 250
    transcript_buffer_max_items: int = 256
    transcript_event_publish_enabled: bool = True
    transcript_persist_partials: bool = False
    transcript_persist_finals: bool = True
    transcript_persist_interrupted: bool = True

    voice_session_max_active: int = 5
    voice_session_ttl_seconds: int = 3600
    voice_session_cleanup_interval_ms: int = 30000

    agent_brain_enabled: bool = True
    agent_brain_provider_purpose: str = "realtime_host"
    agent_brain_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    agent_brain_top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    agent_brain_max_output_tokens: int = Field(default=512, ge=1, le=4096)
    agent_brain_timeout_ms: int = 8000
    agent_brain_enable_json_schema: bool = True
    agent_brain_enable_json_repair_retry: bool = True
    agent_brain_max_json_repair_retries: int = 1

    agent_context_max_tokens: int = 3000
    agent_context_max_recent_turns: int = 8
    agent_context_max_safe_actions: int = 8
    agent_context_max_retrieved_facts: int = 5
    agent_context_max_screen_summary_chars: int = 1200
    agent_context_max_product_summary_chars: int = 1000
    agent_context_max_recipe_step_chars: int = 1200
    agent_context_max_safety_rule_chars: int = 1600
    agent_context_max_user_profile_chars: int = 800

    agent_knowledge_retrieval_enabled: bool = True
    agent_knowledge_retrieval_top_k: int = 5
    agent_knowledge_retrieval_min_score: float = Field(default=0.72, ge=0.0, le=1.0)
    agent_knowledge_retrieval_timeout_ms: int = 120
    agent_knowledge_retrieval_only_on_demand: bool = True

    agent_max_spoken_response_chars: int = 500
    agent_max_normal_sentences: int = 3
    agent_max_screen_explanation_sentences: int = 5
    agent_require_grounded_claims: bool = True
    agent_allow_uncertain_inferences: bool = True
    agent_default_uncertainty_phrase: str = "From what I can verify on screen"

    agent_tool_router_timeout_ms: int = 3000
    agent_browser_action_parallel_with_speech: bool = True
    agent_require_action_id: bool = True
    agent_allow_raw_selector: bool = False
    agent_allow_arbitrary_javascript: bool = False
    agent_type_demo_text_max_chars: int = 120
    browser_runtime_base_url: str = "http://localhost:8200"

    demo_planner_initial_phase: str = "START"
    demo_planner_discovery_min_turns: int = 1
    demo_planner_max_recovery_attempts: int = 2
    demo_planner_auto_summary_after_seconds: int = 900

    persona_tracking_enabled: bool = True
    persona_confidence_decay: float = Field(default=0.95, ge=0.0, le=1.0)
    persona_min_confidence_to_personalize: float = Field(default=0.55, ge=0.0, le=1.0)
    persona_max_interests: int = 10
    persona_max_pain_points: int = 10
    persona_max_objections: int = 10

    memory_updates_enabled: bool = True
    memory_update_min_confidence: float = Field(default=0.55, ge=0.0, le=1.0)
    memory_update_min_importance: float = Field(default=0.50, ge=0.0, le=1.0)
    memory_update_dedupe_similarity_threshold: float = Field(default=0.88, ge=0.0, le=1.0)
    memory_update_max_per_turn: int = 5
    memory_persist_lead_insights: bool = True
    memory_persist_product_facts: bool = False
    memory_dedupe_max_candidates: int = 50

    default_never_click: str = (
        "Delete,Remove,Billing,Invite,Send,Publish,Upgrade,Payment,Account Settings"
    )

    allow_fake_providers_in_production: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("ai_stt_provider")
    @classmethod
    def validate_fake_stt_in_production(cls, value: SttProviderName) -> SttProviderName:
        return value

    def safe_log_dict(self) -> dict[str, object]:
        values = self.model_dump(mode="json")
        redacted: dict[str, object] = {}
        for key, value in values.items():
            lower = key.lower()
            if "secret" in lower or "api_key" in lower or "token" in lower or "password" in lower:
                redacted[key] = "***REDACTED***" if value not in (None, "") else None
            else:
                redacted[key] = value
        return redacted


@lru_cache(maxsize=1)
def get_settings() -> AgentRuntimeSettings:
    settings = AgentRuntimeSettings()
    if (
        settings.app_env == "production"
        and not settings.allow_fake_providers_in_production
        and (settings.ai_stt_provider == "fake" or settings.ai_tts_provider == "fake")
    ):
        msg = "Fake voice providers are blocked in production."
        raise ValueError(msg)
    return settings
