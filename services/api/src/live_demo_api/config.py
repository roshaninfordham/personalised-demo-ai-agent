from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    app_env: str = "local"
    log_level: str = "info"

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
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""
    object_storage_bucket: str = "demo-agent-artifacts"
    object_storage_region: str = "local"
    object_storage_force_path_style: bool = True
    object_storage_auto_create_bucket: bool = True
    object_storage_presigned_url_ttl_seconds: int = 300
    allow_production_bucket_create: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> ServiceSettings:
    return ServiceSettings()
