from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from live_demo_backend_common.ai.types import (
    ProviderCapability,
    ProviderHealth,
    TextGenerationChunk,
    TextGenerationRequest,
    TextGenerationResponse,
)


class TextGenerationProvider(Protocol):
    provider_name: str
    model_name: str
    capabilities: frozenset[ProviderCapability]

    async def health_check(self) -> ProviderHealth: ...

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResponse: ...

    def stream(
        self,
        request: TextGenerationRequest,
    ) -> AsyncIterator[TextGenerationChunk]: ...

    async def tool_call(self, request: TextGenerationRequest) -> TextGenerationResponse: ...

    async def close(self) -> None: ...
