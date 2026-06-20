from __future__ import annotations

from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from live_demo_backend_common.ai.errors import ProviderConfigurationError
from live_demo_backend_common.ai.redaction import is_sensitive_key

TEXT_PROVIDERS = {
    "nvidia_nim",
    "openai",
    "custom_openai_compatible",
    "ollama",
    "fake",
    "disabled",
}
EMBEDDING_PROVIDERS = TEXT_PROVIDERS
VISION_PROVIDERS = TEXT_PROVIDERS


class AiProviderSettings(BaseSettings):
    app_env: str = "local"
    allow_insecure_provider_urls: bool = False
    allow_fake_providers_in_production: bool = False

    ai_text_provider: str = "nvidia_nim"
    ai_text_base_url: str | None = None
    ai_text_api_key: SecretStr | None = None
    ai_text_model: str | None = None
    ai_text_temperature: float = 0.0
    ai_text_top_p: float = 1.0
    ai_text_max_output_tokens: int = 512
    ai_text_max_output_tokens_hard_limit: int = 4096
    ai_text_timeout_ms: int = 8000
    ai_text_enable_streaming: bool = True
    ai_text_enable_tool_calling: bool = True
    ai_text_healthcheck_mode: str = "models"
    ai_text_provider_extra_json: dict[str, Any] = Field(default_factory=dict)
    ai_text_allow_json_schema_downgrade: bool = False

    ai_embedding_provider: str = "ollama"
    ai_embedding_base_url: str | None = None
    ai_embedding_api_key: SecretStr | None = None
    ai_embedding_model: str | None = None
    ai_embedding_dimensions: int = 768
    ai_embedding_batch_size: int = 32
    ai_embedding_max_text_chars: int = 8000
    ai_embedding_timeout_ms: int = 15000
    ai_embedding_cache_enabled: bool = True
    ai_embedding_cache_max_items: int = 10000
    ai_embedding_cache_allow_sensitive: bool = False

    ai_vision_provider: str = "disabled"
    ai_vision_base_url: str | None = None
    ai_vision_api_key: SecretStr | None = None
    ai_vision_model: str | None = None
    ai_vision_timeout_ms: int = 15000
    ai_vision_max_image_size_bytes: int = 3_000_000
    ai_vision_use_only_as_fallback: bool = True
    ai_vision_allow_hot_path: bool = False
    ai_vision_allow_json_schema_downgrade: bool = False

    ollama_base_url: str = "http://ollama:11434"
    ollama_text_model: str | None = None
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_timeout_ms: int = 30000
    ollama_text_mode: str = "openai_compatible"
    ollama_embedding_use_legacy_endpoint: bool = False
    ollama_keep_alive: str = "5m"

    ai_provider_max_connections: int = 100
    ai_provider_max_keepalive_connections: int = 20
    ai_provider_connect_timeout_ms: int = 2000
    ai_provider_read_timeout_ms: int = 8000
    ai_provider_write_timeout_ms: int = 5000
    ai_provider_pool_timeout_ms: int = 1000

    ai_provider_hot_path_max_retries: int = 0
    ai_provider_cold_path_max_retries: int = 2
    ai_provider_retry_base_delay_ms: int = 100
    ai_provider_retry_max_delay_ms: int = 1000
    ai_provider_circuit_failure_threshold: int = 5
    ai_provider_circuit_cooldown_seconds: int = 30

    ai_routing_enabled: bool = False
    ai_debug_log_raw_prompts: bool = False
    ai_debug_log_raw_responses: bool = False
    run_live_provider_tests: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("ai_text_provider")
    @classmethod
    def validate_text_provider(cls, value: str) -> str:
        if value not in TEXT_PROVIDERS:
            raise ValueError(f"Unsupported AI_TEXT_PROVIDER: {value}")
        return value

    @field_validator("ai_embedding_provider")
    @classmethod
    def validate_embedding_provider(cls, value: str) -> str:
        if value not in EMBEDDING_PROVIDERS:
            raise ValueError(f"Unsupported AI_EMBEDDING_PROVIDER: {value}")
        return value

    @field_validator("ai_vision_provider")
    @classmethod
    def validate_vision_provider(cls, value: str) -> str:
        if value not in VISION_PROVIDERS:
            raise ValueError(f"Unsupported AI_VISION_PROVIDER: {value}")
        return value

    @model_validator(mode="after")
    def validate_settings(self) -> AiProviderSettings:
        if self.app_env == "production":
            if (
                "fake"
                in {
                    self.ai_text_provider,
                    self.ai_embedding_provider,
                    self.ai_vision_provider,
                }
                and not self.allow_fake_providers_in_production
            ):
                raise ValueError("Fake providers are disabled in production.")
            object.__setattr__(self, "ai_debug_log_raw_prompts", False)
            object.__setattr__(self, "ai_debug_log_raw_responses", False)

        for url in [
            self.ai_text_base_url,
            self.ai_embedding_base_url,
            self.ai_vision_base_url,
            self.ollama_base_url,
        ]:
            if url:
                validate_provider_base_url(
                    url,
                    app_env=self.app_env,
                    allow_insecure=self.allow_insecure_provider_urls,
                )
        return self

    def safe_log_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        for key, value in self.model_dump(mode="json").items():
            if is_sensitive_key(key):
                payload[key] = "***REDACTED***"
            else:
                payload[key] = value
        return payload


def validate_provider_base_url(
    base_url: str,
    *,
    app_env: str,
    allow_insecure: bool,
) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme in {"file", "javascript", "data", "ftp"}:
        raise ProviderConfigurationError(
            provider_name="configuration",
            model_name=None,
            operation="validate_provider_base_url",
            retryable=False,
            status_code=None,
            safe_message="Provider base URL scheme is not allowed.",
            internal_message=f"Rejected provider base URL scheme: {parsed.scheme}",
        )
    if parsed.scheme not in {"http", "https"}:
        raise ProviderConfigurationError(
            provider_name="configuration",
            model_name=None,
            operation="validate_provider_base_url",
            retryable=False,
            status_code=None,
            safe_message="Provider base URL must use http or https.",
            internal_message=f"Rejected provider base URL: {base_url}",
        )
    if parsed.scheme == "http" and not (
        app_env == "local" or allow_insecure or _is_local_provider_host(parsed.hostname)
    ):
        raise ProviderConfigurationError(
            provider_name="configuration",
            model_name=None,
            operation="validate_provider_base_url",
            retryable=False,
            status_code=None,
            safe_message="Provider base URL must use https outside local development.",
            internal_message=f"Rejected insecure provider base URL: {base_url}",
        )


def _is_local_provider_host(hostname: str | None) -> bool:
    if hostname is None:
        return False
    return hostname in {"localhost", "127.0.0.1", "::1", "ollama"} or hostname.endswith(".local")


@lru_cache(maxsize=1)
def get_ai_provider_settings() -> AiProviderSettings:
    return AiProviderSettings()
