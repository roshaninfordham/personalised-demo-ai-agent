from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from live_demo_backend_common.ai.errors import ProviderCapabilityError
from live_demo_backend_common.ai.types import (
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
    TextGenerationChunk,
    TextGenerationRequest,
    TextGenerationResponse,
)


class DisabledTextProvider:
    provider_name = "disabled"
    model_name = "disabled"
    capabilities: frozenset[ProviderCapability] = frozenset()

    async def close(self) -> None:
        return None

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="text",
            model_name=None,
            status=ProviderStatus.disabled,
            checked_at=datetime.now(UTC),
            safe_message="Text provider is disabled.",
        )

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResponse:
        raise self._error("text.generate")

    async def stream(self, request: TextGenerationRequest) -> AsyncIterator[TextGenerationChunk]:
        raise self._error("text.stream")
        yield

    async def tool_call(self, request: TextGenerationRequest) -> TextGenerationResponse:
        raise self._error("text.tool_call")

    def _error(self, operation: str) -> ProviderCapabilityError:
        return ProviderCapabilityError(
            provider_name=self.provider_name,
            model_name=None,
            operation=operation,
            retryable=False,
            status_code=None,
            safe_message="Text provider is disabled.",
        )
