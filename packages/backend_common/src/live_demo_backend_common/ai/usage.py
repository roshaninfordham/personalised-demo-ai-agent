from __future__ import annotations

from pydantic import BaseModel


class ProviderUsageRecord(BaseModel):
    provider_name: str
    model_name: str | None
    purpose: str | None = None
    latency_ms: int | None = None
    first_token_latency_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    success: bool
    error_code: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
