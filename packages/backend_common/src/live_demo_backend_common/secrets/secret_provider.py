"""Protocol implemented by local and production secret providers."""

from __future__ import annotations

from typing import Protocol

from live_demo_backend_common.secrets.secret_types import SecretProviderHealth, SecretValue


class SecretProvider(Protocol):
    async def get_secret(self, name: str) -> SecretValue:
        ...

    async def get_optional_secret(self, name: str) -> SecretValue | None:
        ...

    async def health_check(self) -> SecretProviderHealth:
        ...
