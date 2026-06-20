from __future__ import annotations

import httpx

from live_demo_backend_common.ai.config import AiProviderSettings


def create_async_http_client(settings: AiProviderSettings) -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        connect=settings.ai_provider_connect_timeout_ms / 1000,
        read=settings.ai_provider_read_timeout_ms / 1000,
        write=settings.ai_provider_write_timeout_ms / 1000,
        pool=settings.ai_provider_pool_timeout_ms / 1000,
    )
    limits = httpx.Limits(
        max_connections=settings.ai_provider_max_connections,
        max_keepalive_connections=settings.ai_provider_max_keepalive_connections,
    )
    return httpx.AsyncClient(timeout=timeout, limits=limits, http2=False)
