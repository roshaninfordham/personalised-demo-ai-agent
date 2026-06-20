"""Bucket creation policy for local development."""

from live_demo_api.config import get_settings
from live_demo_api.storage.artifact_store import ArtifactStore


async def ensure_artifact_bucket_if_allowed(store: ArtifactStore) -> None:
    settings = get_settings()
    if not settings.object_storage_auto_create_bucket:
        return
    if settings.app_env == "production" and not settings.allow_production_bucket_create:
        raise RuntimeError(
            "Refusing to create object-storage bucket in production unless "
            "ALLOW_PRODUCTION_BUCKET_CREATE=true."
        )
    await store.ensure_bucket()
