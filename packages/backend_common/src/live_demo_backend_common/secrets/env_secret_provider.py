"""Environment-backed secret provider for local development and container runtime."""

from __future__ import annotations

import os
from collections.abc import Mapping

from live_demo_backend_common.secrets.secret_errors import SecretNotFoundError
from live_demo_backend_common.secrets.secret_types import SecretProviderHealth, SecretValue


class EnvSecretProvider:
    provider_name = "env"

    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        self._env = env if env is not None else os.environ

    async def get_secret(self, name: str) -> SecretValue:
        value = await self.get_optional_secret(name)
        if value is None:
            raise SecretNotFoundError(f"Required secret is missing: {name}")
        return value

    async def get_optional_secret(self, name: str) -> SecretValue | None:
        value = self._env.get(name)
        if value is None or value == "":
            return None
        return SecretValue(name=name, value=value, source=self.provider_name)

    async def health_check(self) -> SecretProviderHealth:
        return SecretProviderHealth(provider=self.provider_name, healthy=True)
