"""Configuration for the product learner worker."""

from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LearnerWorkerSettings(BaseSettings):
    app_env: str = "local"
    app_name: str = "live-demo-learner-worker"
    log_level: str = "info"

    database_url: str = "postgresql+asyncpg://demo_agent:demo_agent@localhost:5432/demo_agent"
    database_sync_url: str = "postgresql+psycopg://demo_agent:demo_agent@localhost:5432/demo_agent"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout_seconds: int = 30
    database_statement_timeout_ms: int = 5000

    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "live_demo"
    redis_event_stream_maxlen: int = 10000

    learner_enabled: bool = True
    learner_worker_concurrency: int = 2
    learner_job_stream: str = "live_demo:stream:learner:jobs"
    learner_dead_letter_stream: str = "live_demo:stream:learner:dead_letter"
    learner_consumer_group: str = "learner-worker"
    learner_block_ms: int = 5000
    learner_read_count: int = 10
    learner_max_attempts: int = 3
    learner_retry_base_delay_ms: int = 1000
    learner_retry_max_delay_ms: int = 60000
    learner_job_lock_ttl_seconds: int = 600
    learner_run_timeout_seconds: int = 300

    learner_browser_session_ttl_seconds: int = 600
    learner_max_pages_per_product: int = 20
    learner_max_depth: int = 2
    learner_max_actions_per_screen: int = 8
    learner_max_total_actions: int = 50
    learner_action_timeout_ms: int = 5000
    learner_screen_read_timeout_ms: int = 3000
    learner_navigation_timeout_ms: int = 10000
    learner_allow_form_submit: bool = False
    learner_allow_typing: bool = False
    learner_allow_external_navigation: bool = False
    learner_only_low_risk_actions: bool = True
    learner_max_recovery_attempts: int = 2

    first_screen_summary_use_llm: bool = True
    first_screen_summary_use_vision: bool = False
    first_screen_summary_timeout_ms: int = 8000
    first_screen_summary_max_input_chars: int = 8000
    first_screen_summary_max_output_chars: int = 1200

    product_category_detection_use_llm: bool = True
    product_category_detection_timeout_ms: int = 8000
    product_category_min_confidence: float = 0.50

    demo_graph_screen_match_threshold: float = 0.78
    demo_graph_element_match_threshold: float = 0.72
    demo_graph_edge_confidence_min: float = 0.35
    demo_graph_max_nodes_per_product: int = 200
    demo_graph_max_edges_per_product: int = 1000

    generated_route_enabled: bool = True
    generated_route_min_confidence: float = 0.45
    generated_route_max_steps: int = 5
    generated_route_activate_automatically: bool = False

    knowledge_chunking_enabled: bool = True
    knowledge_chunk_max_chars: int = 1200
    knowledge_chunk_overlap_chars: int = 150
    knowledge_chunk_min_chars: int = 150
    knowledge_chunk_dedupe_enabled: bool = True

    knowledge_retrieval_top_k: int = 5
    knowledge_retrieval_min_score: float = 0.72
    knowledge_retrieval_hybrid_enabled: bool = True
    knowledge_retrieval_vector_weight: float = 0.70
    knowledge_retrieval_lexical_weight: float = 0.30
    knowledge_retrieval_timeout_ms: int = 150
    knowledge_embedding_batch_size: int = 32
    ai_embedding_dimensions: int = 768

    scrapegraph_enabled: bool = False
    scrapegraph_install_profile: str = "scrapegraph"
    scrapegraph_use_only_public_urls: bool = True
    scrapegraph_max_pages: int = 3
    scrapegraph_timeout_ms: int = 30000
    scrapegraph_telemetry_enabled: bool = False

    browser_runtime_base_url: str = "http://localhost:8200"
    api_base_url: str = "http://localhost:8000"

    redaction_hash_secret: SecretStr = SecretStr("")
    redaction_customer_name_list: str = ""
    redaction_max_text_chars: int = 100000
    redaction_max_json_depth: int = 10
    redaction_max_json_keys: int = 5000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def safe_log_dict(self) -> dict[str, object]:
        safe: dict[str, object] = {}
        for key, value in self.model_dump().items():
            lowered = key.lower()
            if "secret" in lowered or "token" in lowered or "api_key" in lowered:
                safe[key] = "***REDACTED***"
            else:
                safe[key] = value
        return safe


ServiceSettings = LearnerWorkerSettings


@lru_cache(maxsize=1)
def get_settings() -> LearnerWorkerSettings:
    return LearnerWorkerSettings()
