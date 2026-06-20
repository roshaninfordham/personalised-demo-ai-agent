from __future__ import annotations

from dataclasses import dataclass

import httpx

from live_demo_backend_common.ai.redaction import redact_mapping


@dataclass(slots=True)
class ProviderError(Exception):
    provider_name: str
    model_name: str | None
    operation: str
    retryable: bool
    status_code: int | None
    safe_message: str
    internal_message: str | None = None
    trace_id: str | None = None

    def __str__(self) -> str:
        return self.safe_message

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "operation": self.operation,
            "retryable": self.retryable,
            "status_code": self.status_code,
            "safe_message": self.safe_message,
            "trace_id": self.trace_id,
        }


class ProviderConfigurationError(ProviderError):
    pass


class ProviderAuthenticationError(ProviderError):
    pass


class ProviderAuthorizationError(ProviderError):
    pass


class ProviderRateLimitError(ProviderError):
    pass


class ProviderTimeoutError(ProviderError):
    pass


class ProviderUnavailableError(ProviderError):
    pass


class ProviderBadRequestError(ProviderError):
    pass


class ProviderResponseValidationError(ProviderError):
    pass


class ProviderStreamingError(ProviderError):
    pass


class ProviderCapabilityError(ProviderError):
    pass


class ProviderCircuitOpenError(ProviderError):
    pass


def provider_error_from_http_status(
    *,
    provider_name: str,
    model_name: str | None,
    operation: str,
    status_code: int,
    response_text: str,
    trace_id: str | None = None,
) -> ProviderError:
    redacted = redact_mapping({"response_text": response_text})["response_text"]
    internal_message = str(redacted)
    if status_code == 400:
        return ProviderBadRequestError(
            provider_name=provider_name,
            model_name=model_name,
            operation=operation,
            retryable=False,
            status_code=status_code,
            safe_message="Provider rejected the request.",
            internal_message=internal_message,
            trace_id=trace_id,
        )
    if status_code == 401:
        return ProviderAuthenticationError(
            provider_name=provider_name,
            model_name=model_name,
            operation=operation,
            retryable=False,
            status_code=status_code,
            safe_message="Provider authentication failed.",
            internal_message=internal_message,
            trace_id=trace_id,
        )
    if status_code == 403:
        return ProviderAuthorizationError(
            provider_name=provider_name,
            model_name=model_name,
            operation=operation,
            retryable=False,
            status_code=status_code,
            safe_message="Provider authorization failed.",
            internal_message=internal_message,
            trace_id=trace_id,
        )
    if status_code == 408:
        return ProviderTimeoutError(
            provider_name=provider_name,
            model_name=model_name,
            operation=operation,
            retryable=True,
            status_code=status_code,
            safe_message="Provider timed out.",
            internal_message=internal_message,
            trace_id=trace_id,
        )
    if status_code == 429:
        return ProviderRateLimitError(
            provider_name=provider_name,
            model_name=model_name,
            operation=operation,
            retryable=True,
            status_code=status_code,
            safe_message="Provider rate limit exceeded.",
            internal_message=internal_message,
            trace_id=trace_id,
        )
    if status_code in {409, 500, 502, 503, 504}:
        return ProviderUnavailableError(
            provider_name=provider_name,
            model_name=model_name,
            operation=operation,
            retryable=True,
            status_code=status_code,
            safe_message="Provider is temporarily unavailable.",
            internal_message=internal_message,
            trace_id=trace_id,
        )
    return ProviderUnavailableError(
        provider_name=provider_name,
        model_name=model_name,
        operation=operation,
        retryable=status_code >= 500,
        status_code=status_code,
        safe_message="Provider returned an unexpected error.",
        internal_message=internal_message,
        trace_id=trace_id,
    )


def provider_error_from_httpx_exception(
    *,
    provider_name: str,
    model_name: str | None,
    operation: str,
    exc: httpx.HTTPError,
    trace_id: str | None = None,
) -> ProviderError:
    base = {
        "provider_name": provider_name,
        "model_name": model_name,
        "operation": operation,
        "status_code": None,
        "internal_message": redact_mapping({"error": str(exc)})["error"],
        "trace_id": trace_id,
    }
    if isinstance(exc, httpx.TimeoutException):
        return ProviderTimeoutError(
            retryable=True,
            safe_message="Provider request timed out.",
            **base,
        )
    return ProviderUnavailableError(
        retryable=True,
        safe_message="Provider network request failed.",
        **base,
    )
