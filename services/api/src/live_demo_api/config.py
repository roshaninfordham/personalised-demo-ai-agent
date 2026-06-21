from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    app_env: str = "local"
    app_name: str = "live-demo-agent-api"
    log_level: str = "info"
    api_host: str = "0.0.0.0"  # noqa: S104 - local Docker/dev server bind address.
    api_port: int = 8000
    api_workers: int = 1
    api_enable_docs: bool = True
    api_request_timeout_ms: int = 30000
    api_max_request_body_bytes: int = 1048576

    database_url: str = "postgresql+asyncpg://demo_agent:demo_agent@localhost:5432/demo_agent"
    database_sync_url: str = "postgresql+psycopg://demo_agent:demo_agent@localhost:5432/demo_agent"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout_seconds: int = 30
    database_statement_timeout_ms: int = 5000
    allow_production_migrations: bool = False

    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "live_demo"
    redis_session_ttl_seconds: int = 86400
    redis_lock_ttl_ms: int = 10000
    redis_transcript_window_max_entries: int = 32
    redis_event_stream_maxlen: int = 10000

    event_bus_provider: str = "redis_streams"
    event_bus_publish_global: bool = True
    event_bus_consumer_group: str = "api"
    event_bus_consumer_name: str = "api-local-1"
    event_bus_block_ms: int = 5000
    event_bus_read_count: int = 20
    event_bus_max_delivery_attempts: int = 5
    event_bus_processed_event_ttl_seconds: int = 86400

    object_storage_provider: str = "minio"
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_access_key: SecretStr = SecretStr("")
    object_storage_secret_key: SecretStr = SecretStr("")
    object_storage_bucket: str = "demo-agent-artifacts"
    object_storage_region: str = "local"
    object_storage_force_path_style: bool = True
    object_storage_auto_create_bucket: bool = True
    object_storage_presigned_url_ttl_seconds: int = 300
    allow_production_bucket_create: bool = False

    auth_provider: str = "local"
    cors_allowed_origins: str = "http://localhost:3000"
    transport_provider: str = "small_webrtc"
    transport_room_ttl_seconds: int = 3600

    dev_allow_implicit_local_org: bool = True
    dev_local_organization_id: str = "00000000-0000-0000-0000-000000000001"
    dev_local_user_id: str = "00000000-0000-0000-0000-000000000002"
    dev_local_user_role: str = "owner"

    allow_local_product_urls: bool = False
    max_product_url_length: int = 2048

    default_page_limit: int = 25
    max_page_limit: int = 100
    max_transcript_page_limit: int = 500
    max_cursor_length: int = 2048

    guidance_max_content_bytes: int = 131072
    guidance_max_json_depth: int = 10
    guidance_max_json_keys: int = 1000

    recipe_max_steps: int = 50
    recipe_max_never_click_items: int = 100
    recipe_max_text_field_length: int = 2000
    recipe_engine_enabled: bool = True
    recipe_max_allowed_actions: int = 100
    recipe_max_allowed_domains: int = 50
    recipe_max_allowed_form_fields: int = 100
    recipe_max_json_bytes: int = 262144
    recipe_max_json_depth: int = 12
    recipe_max_json_keys: int = 5000
    recipe_generation_enabled: bool = True
    recipe_generation_use_llm: bool = True
    recipe_generation_provider_purpose: str = "recipe_generation"
    recipe_generation_temperature: float = 0.0
    recipe_generation_top_p: float = 1.0
    recipe_generation_max_output_tokens: int = 2500
    recipe_generation_timeout_ms: int = 15000
    recipe_generation_max_repair_retries: int = 1
    recipe_generation_require_validation: bool = True
    recipe_compiler_cache_enabled: bool = True
    recipe_compiler_recompile_on_update: bool = True
    recipe_compiler_max_compiled_payload_bytes: int = 65536
    recipe_compiler_include_talk_track: bool = True
    recipe_compiler_include_success_criteria: bool = True
    recipe_screen_match_threshold: float = 0.72
    recipe_action_match_threshold: float = 0.70
    recipe_match_cache_enabled: bool = True
    recipe_match_cache_ttl_seconds: int = 3600
    recipe_match_max_candidate_screens: int = 50
    recipe_match_max_candidate_actions: int = 50
    recipe_progress_enabled: bool = True
    recipe_progress_persist_every_update: bool = True
    recipe_progress_max_attempts_per_step: int = 3
    recipe_progress_auto_skip_blocked_steps: bool = False
    recipe_fallback_enabled: bool = True
    recipe_fallback_max_attempts: int = 2
    recipe_fallback_allow_go_back: bool = True
    recipe_fallback_allow_read_screen: bool = True
    recipe_fallback_allow_safe_alternative: bool = True
    recipe_fallback_ask_user_on_low_confidence: bool = True

    rate_limit_enabled: bool = False
    rate_limit_default_per_minute: int = 120
    enable_tracing: bool = False

    policy_engine_enabled: bool = True
    policy_fail_closed: bool = True
    policy_debug_endpoints_enabled: bool = False
    policy_max_text_chars: int = 8000
    policy_max_rules_per_recipe: int = 100

    allow_destructive_actions: bool = False
    require_confirmation_for_high_risk: bool = True
    allow_payment_pages: bool = False
    allow_external_navigation: bool = False
    allow_account_settings_actions: bool = False
    action_policy_confirmation_ttl_seconds: int = 120

    rbac_enabled: bool = True
    rbac_local_dev_allow_header_principal: bool = True
    rbac_agent_runtime_role: str = "agent_runtime"

    audit_logging_enabled: bool = True
    audit_fail_closed_for_high_risk: bool = True
    audit_hash_chain_enabled: bool = False
    audit_metadata_max_bytes: int = 32768
    audit_read_max_page_size: int = 100

    redaction_enabled: bool = True
    redaction_hash_secret: SecretStr = SecretStr("")
    redaction_fail_on_secret_in_prompt: bool = True
    redaction_max_text_chars: int = 100000
    redaction_max_json_depth: int = 10
    redaction_max_json_keys: int = 5000
    redaction_customer_name_list: str = ""
    redaction_visual_screenshot_redaction_enabled: bool = False

    learner_enabled: bool = True
    learner_job_stream: str = "live_demo:stream:learner:jobs"
    learner_consumer_group: str = "learner-worker"
    learner_max_attempts: int = 3
    learner_job_enqueue_maxlen: int = 10000
    generated_route_activate_automatically: bool = False
    knowledge_retrieval_top_k: int = 5
    knowledge_retrieval_min_score: float = 0.72

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def safe_log_dict(self) -> dict[str, object]:
        safe: dict[str, object] = {}
        for key, value in self.model_dump().items():
            lowered = key.lower()
            if (
                "secret" in lowered
                or "token" in lowered
                or "api_key" in lowered
                or isinstance(value, SecretStr)
            ):
                safe[key] = "***REDACTED***"
            else:
                safe[key] = value
        return safe


ServiceSettings = ApiSettings


@lru_cache(maxsize=1)
def get_settings() -> ApiSettings:
    return ApiSettings()
