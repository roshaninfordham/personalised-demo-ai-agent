"""Safe artifact content routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from starlette.responses import Response

from live_demo_api.dependencies import get_artifact_store
from live_demo_api.errors import ValidationAppError
from live_demo_api.storage.artifact_store import ArtifactStore

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])


@router.get("/browser-screenshot")
async def get_browser_screenshot(
    object_key: Annotated[str, Query(min_length=1, max_length=1024)],
    artifact_store: Annotated[ArtifactStore, Depends(get_artifact_store)],
) -> Response:
    safe_key = _validate_browser_screenshot_key(object_key)
    content = await artifact_store.get_bytes(safe_key)
    return Response(
        content=content,
        media_type=_content_type_for_key(safe_key),
        headers={
            "Cache-Control": "private, max-age=60",
            "X-Content-Type-Options": "nosniff",
        },
    )


def _validate_browser_screenshot_key(object_key: str) -> str:
    key = object_key.strip()
    if (
        not key
        or key.startswith("/")
        or "\\" in key
        or ".." in key.split("/")
        or "screenshots/" not in key
    ):
        raise ValidationAppError(
            "Invalid screenshot artifact key.",
            code="invalid_artifact_key",
        )
    return key


def _content_type_for_key(object_key: str) -> str:
    lowered = object_key.lower()
    if lowered.endswith(".png"):
        return "image/png"
    if lowered.endswith(".jpg") or lowered.endswith(".jpeg"):
        return "image/jpeg"
    return "image/webp"
