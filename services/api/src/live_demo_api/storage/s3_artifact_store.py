"""S3-compatible artifact storage using boto3 behind async wrappers."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Mapping
from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.config import Config  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from live_demo_api.config import ServiceSettings, get_settings
from live_demo_api.storage.artifact_store import StoredObject

SECRET_METADATA_TOKENS = ("secret", "token", "password", "key", "credential")


class ArtifactStorageError(RuntimeError):
    """Raised when object storage operations fail."""


def _safe_metadata(metadata: Mapping[str, str] | None) -> dict[str, str]:
    if metadata is None:
        return {}
    safe: dict[str, str] = {}
    for key, value in metadata.items():
        lowered = key.lower()
        if any(token in lowered for token in SECRET_METADATA_TOKENS):
            raise ValueError("Object metadata must not contain secrets")
        safe[key] = value
    return safe


class S3ArtifactStore:
    def __init__(self, settings: ServiceSettings | None = None) -> None:
        self._settings = settings or get_settings()
        addressing_style = "path" if self._settings.object_storage_force_path_style else "auto"
        self._client: Any = boto3.client(
            "s3",
            endpoint_url=self._settings.object_storage_endpoint,
            aws_access_key_id=self._settings.object_storage_access_key.get_secret_value(),
            aws_secret_access_key=self._settings.object_storage_secret_key.get_secret_value(),
            region_name=self._settings.object_storage_region,
            config=Config(s3={"addressing_style": addressing_style}),
        )

    @property
    def bucket(self) -> str:
        return self._settings.object_storage_bucket

    async def ensure_bucket(self) -> None:
        def ensure() -> None:
            try:
                self._client.head_bucket(Bucket=self.bucket)
            except ClientError as exc:
                code = str(exc.response.get("Error", {}).get("Code", ""))
                if code not in {"404", "NoSuchBucket", "NotFound"}:
                    raise
                self._client.create_bucket(Bucket=self.bucket)

        await asyncio.to_thread(ensure)

    async def put_bytes(
        self,
        object_key: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredObject:
        sha256_hex = hashlib.sha256(content).hexdigest()
        safe_metadata = _safe_metadata(metadata)

        def put() -> str | None:
            response = self._client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=content,
                ContentType=content_type,
                Metadata=safe_metadata,
            )
            etag = response.get("ETag")
            return str(etag).strip('"') if etag is not None else None

        etag = await asyncio.to_thread(put)
        return StoredObject(
            bucket=self.bucket,
            object_key=object_key,
            content_type=content_type,
            size_bytes=len(content),
            sha256_hex=sha256_hex,
            etag=etag,
        )

    async def get_bytes(self, object_key: str) -> bytes:
        def get() -> bytes:
            response = self._client.get_object(Bucket=self.bucket, Key=object_key)
            body = response["Body"].read()
            if not isinstance(body, bytes):
                raise ArtifactStorageError("S3 get_object body did not return bytes")
            return body

        return await asyncio.to_thread(get)

    async def delete_object(self, object_key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=self.bucket, Key=object_key)

    async def create_presigned_get_url(self, object_key: str, expires_seconds: int) -> str:
        max_ttl = self._settings.object_storage_presigned_url_ttl_seconds
        if expires_seconds <= 0 or expires_seconds > max_ttl:
            raise ValueError(f"Presigned URL expiry must be between 1 and {max_ttl} seconds")

        def create_url() -> str:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expires_seconds,
            )
            if not isinstance(url, str) or not url:
                raise ArtifactStorageError("S3 client returned an invalid presigned URL")
            return url

        return await asyncio.to_thread(create_url)
