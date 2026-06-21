"""Resource health classification helpers."""

from __future__ import annotations

from live_demo_api.orchestration.orchestration_types import SessionResource


def resource_is_active(resource: SessionResource) -> bool:
    return resource.status in {"allocating", "allocated", "ready", "releasing"}


def resource_is_ready(resource: SessionResource) -> bool:
    return resource.status == "ready"
