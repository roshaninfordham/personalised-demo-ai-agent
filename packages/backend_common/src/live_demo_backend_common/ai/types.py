from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from live_demo_backend_common.ai.redaction import is_sensitive_key


class ProviderStatus(StrEnum):
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"
    disabled = "disabled"


class ProviderCapability(StrEnum):
    text_generate = "text_generate"
    text_stream = "text_stream"
    tool_calling = "tool_calling"
    embeddings = "embeddings"
    vision = "vision"
    json_schema_output = "json_schema_output"


class MessageRole(StrEnum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class TextGenerationFinishReason(StrEnum):
    stop = "stop"
    length = "length"
    tool_calls = "tool_calls"
    content_filter = "content_filter"
    error = "error"
    unknown = "unknown"


class ProviderHealth(BaseModel):
    provider_name: str
    provider_type: str
    model_name: str | None = None
    status: ProviderStatus
    latency_ms: int | None = None
    capabilities: list[ProviderCapability] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    safe_message: str


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class ToolFunctionSchema(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if re.fullmatch(r"^[a-zA-Z0-9_-]{1,64}$", value) is None:
            raise ValueError("Tool function name must match ^[a-zA-Z0-9_-]{1,64}$.")
        return value

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, value: dict[str, Any]) -> dict[str, Any]:
        if value.get("type") != "object":
            raise ValueError("Tool parameters must be a JSON Schema object.")
        copied = dict(value)
        copied.setdefault("additionalProperties", False)
        return copied


class ToolDefinition(BaseModel):
    type: Literal["function"] = "function"
    function: ToolFunctionSchema


class ToolCall(BaseModel):
    id: str
    name: str
    arguments_json: str
    arguments: dict[str, Any] | None = None

    @classmethod
    def from_arguments_json(cls, *, id: str, name: str, arguments_json: str) -> ToolCall:
        try:
            parsed = json.loads(arguments_json or "{}")
        except json.JSONDecodeError:
            parsed = None
        if parsed is not None and not isinstance(parsed, dict):
            parsed = None
        return cls(id=id, name=name, arguments_json=arguments_json, arguments=parsed)


class TextGenerationRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    model: str | None = None
    system_prompt: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_output_tokens: int = Field(default=512, ge=1, le=4096)
    response_format: Literal["text", "json_object", "json_schema"] = "text"
    json_schema: dict[str, Any] | None = None
    tools: list[ToolDefinition] = Field(default_factory=list)
    tool_choice: Literal["none", "auto", "required"] | dict[str, Any] = "auto"
    timeout_ms: int | None = Field(default=None, gt=0)
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self) -> TextGenerationRequest:
        if self.response_format == "json_schema" and self.json_schema is None:
            raise ValueError("json_schema is required when response_format=json_schema.")
        for key, value in self.metadata.items():
            if is_sensitive_key(key) or is_sensitive_key(value):
                raise ValueError("Provider request metadata must not contain secrets.")
        return self


class TokenUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class TextGenerationResponse(BaseModel):
    provider_name: str
    model_name: str
    content: str
    finish_reason: TextGenerationFinishReason
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: TokenUsage | None = None
    latency_ms: int
    first_token_latency_ms: int | None = None
    request_id: str | None = None
    raw_response_hash: str | None = None


class TextGenerationChunk(BaseModel):
    provider_name: str
    model_name: str
    delta_text: str = ""
    tool_call_delta: dict[str, Any] | None = None
    is_final: bool = False
    finish_reason: TextGenerationFinishReason | None = None
    usage: TokenUsage | None = None
    latency_ms: int | None = None
    first_token_latency_ms: int | None = None
    request_id: str | None = None


class EmbeddingRequest(BaseModel):
    texts: list[str] = Field(min_length=1)
    model: str | None = None
    dimensions: int | None = Field(default=None, gt=0)
    normalize: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata(self) -> EmbeddingRequest:
        for key, value in self.metadata.items():
            if is_sensitive_key(key) or is_sensitive_key(value):
                raise ValueError("Embedding request metadata must not contain secrets.")
        return self


class EmbeddingVector(BaseModel):
    text_index: int
    vector: list[float]
    dimensions: int
    l2_norm: float

    @field_validator("vector")
    @classmethod
    def validate_finite_vector(cls, value: list[float]) -> list[float]:
        if any(not math.isfinite(item) for item in value):
            raise ValueError("Embedding vectors must contain finite values.")
        return value


class EmbeddingResponse(BaseModel):
    provider_name: str
    model_name: str
    vectors: list[EmbeddingVector]
    usage: TokenUsage | None = None
    latency_ms: int


class ImageInput(BaseModel):
    image_bytes: bytes | None = None
    image_base64: str | None = None
    content_type: Literal["image/png", "image/jpeg", "image/webp"]
    source_artifact_id: str | None = None

    @model_validator(mode="after")
    def validate_source(self) -> ImageInput:
        source_count = sum(
            value is not None
            for value in [self.image_bytes, self.image_base64, self.source_artifact_id]
        )
        if source_count != 1:
            raise ValueError("Exactly one image source must be provided.")
        return self


class VisionDescriptionRequest(BaseModel):
    image: ImageInput
    prompt: str
    max_output_tokens: int = Field(default=512, ge=1, le=4096)
    metadata: dict[str, str] = Field(default_factory=dict)


class VisionDescriptionResponse(BaseModel):
    provider_name: str
    model_name: str | None
    description: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    latency_ms: int


class UiVisionFact(BaseModel):
    fact_type: Literal["button", "input", "nav", "chart", "table", "text", "unknown"]
    label: str | None = None
    bbox: dict[str, float] | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class UiVisionExtractionRequest(BaseModel):
    image: ImageInput
    prompt: str = "Extract visible UI facts from this screenshot."
    max_output_tokens: int = Field(default=512, ge=1, le=4096)
    metadata: dict[str, str] = Field(default_factory=dict)


class UiVisionExtractionResponse(BaseModel):
    provider_name: str
    model_name: str | None
    facts: list[UiVisionFact] = Field(default_factory=list)
    summary: str
    latency_ms: int
