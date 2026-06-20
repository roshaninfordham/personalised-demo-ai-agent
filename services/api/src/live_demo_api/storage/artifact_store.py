"""Provider-agnostic artifact store interface."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    object_key: str
    content_type: str
    size_bytes: int
    sha256_hex: str
    etag: str | None


class ArtifactStore(Protocol):
    async def ensure_bucket(self) -> None: ...

    async def put_bytes(
        self,
        object_key: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredObject: ...

    async def get_bytes(self, object_key: str) -> bytes: ...

    async def delete_object(self, object_key: str) -> None: ...

    async def create_presigned_get_url(self, object_key: str, expires_seconds: int) -> str: ...
