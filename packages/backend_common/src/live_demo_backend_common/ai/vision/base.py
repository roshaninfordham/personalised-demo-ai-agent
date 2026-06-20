from __future__ import annotations

import base64
import binascii
from typing import Protocol

from live_demo_backend_common.ai.errors import ProviderBadRequestError
from live_demo_backend_common.ai.types import (
    ImageInput,
    ProviderHealth,
    UiVisionExtractionRequest,
    UiVisionExtractionResponse,
    VisionDescriptionRequest,
    VisionDescriptionResponse,
)


class VisionUnderstandingProvider(Protocol):
    provider_name: str
    model_name: str | None

    async def health_check(self) -> ProviderHealth: ...

    async def describe_image(
        self,
        request: VisionDescriptionRequest,
    ) -> VisionDescriptionResponse: ...

    async def extract_ui_facts(
        self,
        request: UiVisionExtractionRequest,
    ) -> UiVisionExtractionResponse: ...

    async def close(self) -> None: ...


def image_bytes_from_input(
    image: ImageInput,
    *,
    provider_name: str,
    model_name: str | None,
    max_size_bytes: int,
) -> bytes:
    if image.source_artifact_id is not None:
        raise ProviderBadRequestError(
            provider_name=provider_name,
            model_name=model_name,
            operation="vision.read_image",
            retryable=False,
            status_code=None,
            safe_message="Vision adapter cannot resolve artifact references directly.",
        )
    if image.image_bytes is not None:
        payload = image.image_bytes
    elif image.image_base64 is not None:
        try:
            payload = base64.b64decode(image.image_base64, validate=True)
        except binascii.Error as exc:
            raise ProviderBadRequestError(
                provider_name=provider_name,
                model_name=model_name,
                operation="vision.read_image",
                retryable=False,
                status_code=None,
                safe_message="Image base64 payload is invalid.",
            ) from exc
    else:
        payload = b""
    if len(payload) > max_size_bytes:
        raise ProviderBadRequestError(
            provider_name=provider_name,
            model_name=model_name,
            operation="vision.read_image",
            retryable=False,
            status_code=None,
            safe_message="Image exceeds configured maximum size.",
        )
    return payload


def image_data_uri(
    image: ImageInput,
    *,
    provider_name: str,
    model_name: str | None,
    max_size_bytes: int,
) -> str:
    payload = image_bytes_from_input(
        image,
        provider_name=provider_name,
        model_name=model_name,
        max_size_bytes=max_size_bytes,
    )
    return f"data:{image.content_type};base64,{base64.b64encode(payload).decode('ascii')}"
