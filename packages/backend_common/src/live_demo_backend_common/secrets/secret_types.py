"""Types shared by secret providers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecretValue:
    name: str
    value: str
    source: str

    def __repr__(self) -> str:
        return f"SecretValue(name={self.name!r}, value='***REDACTED***', source={self.source!r})"

    def __str__(self) -> str:
        return "***REDACTED***"

    def reveal(self) -> str:
        return self.value


@dataclass(frozen=True)
class SecretProviderHealth:
    provider: str
    healthy: bool
    error_code: str | None = None
    safe_message: str | None = None
