from __future__ import annotations

from live_demo_backend_common.ai.errors import (
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderRateLimitError,
    provider_error_from_http_status,
)


def test_http_error_mapping() -> None:
    assert isinstance(
        provider_error_from_http_status(
            provider_name="p",
            model_name="m",
            operation="op",
            status_code=400,
            response_text="bad",
        ),
        ProviderBadRequestError,
    )
    assert isinstance(
        provider_error_from_http_status(
            provider_name="p",
            model_name="m",
            operation="op",
            status_code=401,
            response_text="secret token",
        ),
        ProviderAuthenticationError,
    )
    assert isinstance(
        provider_error_from_http_status(
            provider_name="p",
            model_name="m",
            operation="op",
            status_code=429,
            response_text="rate",
        ),
        ProviderRateLimitError,
    )
