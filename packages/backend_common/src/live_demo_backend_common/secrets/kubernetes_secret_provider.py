"""Kubernetes Secret provider wrapper.

Kubernetes injects secrets into containers as environment variables or mounted files.
Phase 16 supports the environment-variable mode directly and keeps this provider as
the production-facing abstraction so a future External Secrets backend can be added
without changing callers.
"""

from __future__ import annotations

from collections.abc import Mapping

from live_demo_backend_common.secrets.env_secret_provider import EnvSecretProvider


class KubernetesSecretProvider(EnvSecretProvider):
    provider_name = "kubernetes_secret"

    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        super().__init__(env=env)
