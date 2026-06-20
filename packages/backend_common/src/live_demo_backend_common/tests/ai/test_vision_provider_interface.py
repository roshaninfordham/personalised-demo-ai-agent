from __future__ import annotations

import base64

import pytest

from live_demo_backend_common.ai.errors import ProviderBadRequestError, ProviderCapabilityError
from live_demo_backend_common.ai.types import (
    ImageInput,
    UiVisionExtractionRequest,
    VisionDescriptionRequest,
)
from live_demo_backend_common.ai.vision.base import image_bytes_from_input
from live_demo_backend_common.ai.vision.disabled import DisabledVisionProvider
from live_demo_backend_common.ai.vision.fake import FakeVisionProvider
from live_demo_backend_common.ai.vision.openai_compatible import OpenAICompatibleVisionProvider
from live_demo_backend_common.tests.ai.helpers import mock_client, test_settings


@pytest.mark.asyncio
async def test_disabled_vision_provider_raises_capability_error() -> None:
    provider = DisabledVisionProvider()
    request = VisionDescriptionRequest(
        image=ImageInput(image_bytes=b"123", content_type="image/png"),
        prompt="describe",
    )
    with pytest.raises(ProviderCapabilityError):
        await provider.describe_image(request)


def test_image_validation_rejects_oversized_and_artifact_reference() -> None:
    with pytest.raises(ProviderBadRequestError):
        image_bytes_from_input(
            ImageInput(image_bytes=b"1234", content_type="image/png"),
            provider_name="vision",
            model_name="model",
            max_size_bytes=3,
        )
    with pytest.raises(ProviderBadRequestError):
        image_bytes_from_input(
            ImageInput(source_artifact_id="artifact", content_type="image/png"),
            provider_name="vision",
            model_name="model",
            max_size_bytes=10,
        )


@pytest.mark.asyncio
async def test_fake_vision_provider_is_deterministic() -> None:
    provider = FakeVisionProvider()
    response = await provider.extract_ui_facts(
        UiVisionExtractionRequest(
            image=ImageInput(
                image_base64=base64.b64encode(b"img").decode(),
                content_type="image/png",
            ),
            metadata={"fake_summary": "summary"},
        )
    )
    assert response.summary == "summary"


@pytest.mark.asyncio
async def test_openai_compatible_vision_maps_image_to_data_uri() -> None:
    provider = OpenAICompatibleVisionProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key=None,
        model_name="vision-model",
        settings=test_settings(ai_vision_max_image_size_bytes=100),
        client=mock_client(
            lambda request: __import__("httpx").Response(
                200,
                json={"choices": [{"message": {"content": "visible UI"}, "finish_reason": "stop"}]},
            )
        ),
    )
    response = await provider.describe_image(
        VisionDescriptionRequest(
            image=ImageInput(image_bytes=b"img", content_type="image/png"),
            prompt="describe",
        )
    )
    assert response.description == "visible UI"
