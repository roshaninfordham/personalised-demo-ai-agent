from __future__ import annotations

from collections import OrderedDict
from typing import Protocol

from live_demo_backend_common.ai.redaction import safe_hash_text
from live_demo_backend_common.ai.types import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingVector,
    ProviderHealth,
)


class EmbeddingProvider(Protocol):
    provider_name: str
    model_name: str
    dimensions: int

    async def health_check(self) -> ProviderHealth: ...

    async def embed_texts(self, request: EmbeddingRequest) -> EmbeddingResponse: ...

    async def close(self) -> None: ...


class EmbeddingCache:
    def __init__(self, max_items: int) -> None:
        self._max_items = max_items
        self._items: OrderedDict[str, EmbeddingVector] = OrderedDict()

    def get(self, key: str) -> EmbeddingVector | None:
        value = self._items.get(key)
        if value is not None:
            self._items.move_to_end(key)
        return value

    def put(self, key: str, value: EmbeddingVector) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        while len(self._items) > self._max_items:
            self._items.popitem(last=False)


def embedding_cache_key(
    *,
    provider_name: str,
    model_name: str,
    dimensions: int,
    normalize: bool,
    text: str,
) -> str:
    return safe_hash_text(f"{provider_name}:{model_name}:{dimensions}:{normalize}:{text}")
