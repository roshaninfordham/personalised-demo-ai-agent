"""Safe agent runtime errors."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentRuntimeError(Exception):
    code: str
    safe_message: str
    status_code: int = 500
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.safe_message


class ConfigurationError(AgentRuntimeError):
    def __init__(self, safe_message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__("configuration_error", safe_message, 500, details or {})


class VoiceSessionNotFoundError(AgentRuntimeError):
    def __init__(self) -> None:
        super().__init__("voice_session_not_found", "Voice session not found.", 404)


class VoiceSessionLimitError(AgentRuntimeError):
    def __init__(self) -> None:
        super().__init__("voice_session_limit_reached", "Voice session limit reached.", 429)


class VoiceSessionStateError(AgentRuntimeError):
    def __init__(self, safe_message: str) -> None:
        super().__init__("voice_session_invalid_transition", safe_message, 409)


class ProviderUnavailableError(AgentRuntimeError):
    def __init__(self, provider_name: str, safe_message: str = "Provider unavailable.") -> None:
        super().__init__(
            "provider_unavailable",
            safe_message,
            503,
            {"provider_name": provider_name},
        )


class ProviderCapabilityError(AgentRuntimeError):
    def __init__(self, provider_name: str, safe_message: str) -> None:
        super().__init__(
            "provider_capability_unavailable",
            safe_message,
            501,
            {"provider_name": provider_name},
        )
