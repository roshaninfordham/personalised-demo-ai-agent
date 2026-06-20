from __future__ import annotations

from datetime import UTC, datetime

from live_demo_backend_common.ai.types import (
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
    UiVisionExtractionRequest,
    UiVisionExtractionResponse,
    VisionDescriptionRequest,
    VisionDescriptionResponse,
)


class FakeVisionProvider:
    provider_name = "fake"
    model_name: str | None = "fake-vision-model"
    capabilities = frozenset({ProviderCapability.vision})

    async def close(self) -> None:
        return None

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="vision",
            model_name=self.model_name,
            status=ProviderStatus.healthy,
            capabilities=list(self.capabilities),
            checked_at=datetime.now(UTC),
            safe_message="Fake vision provider is healthy.",
        )

    async def describe_image(
        self,
        request: VisionDescriptionRequest,
    ) -> VisionDescriptionResponse:
        return VisionDescriptionResponse(
            provider_name=self.provider_name,
            model_name=self.model_name,
            description=request.metadata.get("fake_description", "fake image description"),
            latency_ms=0,
        )

    async def extract_ui_facts(
        self,
        request: UiVisionExtractionRequest,
    ) -> UiVisionExtractionResponse:
        return UiVisionExtractionResponse(
            provider_name=self.provider_name,
            model_name=self.model_name,
            facts=[],
            summary=request.metadata.get("fake_summary", "fake UI facts"),
            latency_ms=0,
        )
