from __future__ import annotations

from datetime import UTC, datetime

from live_demo_backend_common.ai.errors import ProviderCapabilityError
from live_demo_backend_common.ai.types import (
    ProviderHealth,
    ProviderStatus,
    UiVisionExtractionRequest,
    UiVisionExtractionResponse,
    VisionDescriptionRequest,
    VisionDescriptionResponse,
)


class DisabledVisionProvider:
    provider_name = "disabled"
    model_name: str | None = None

    async def close(self) -> None:
        return None

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="vision",
            model_name=None,
            status=ProviderStatus.disabled,
            checked_at=datetime.now(UTC),
            safe_message="Vision provider is disabled.",
        )

    async def describe_image(
        self,
        request: VisionDescriptionRequest,
    ) -> VisionDescriptionResponse:
        raise self._error("vision.describe_image")

    async def extract_ui_facts(
        self,
        request: UiVisionExtractionRequest,
    ) -> UiVisionExtractionResponse:
        raise self._error("vision.extract_ui_facts")

    def _error(self, operation: str) -> ProviderCapabilityError:
        return ProviderCapabilityError(
            provider_name=self.provider_name,
            model_name=None,
            operation=operation,
            retryable=False,
            status_code=None,
            safe_message="Vision provider is disabled.",
        )
