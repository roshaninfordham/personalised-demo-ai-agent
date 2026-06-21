"""Safe orchestration event publishing wrappers."""

from __future__ import annotations

from uuid import UUID

from live_demo_api.events.event_bus import EventBus
from live_demo_api.security import RequestContext
from live_demo_api.services.audit_service import publish_event


async def publish_orchestration_event(
    event_bus: EventBus,
    *,
    organization_id: UUID,
    session_id: UUID,
    event_type: str,
    request_context: RequestContext,
    payload: dict[str, object],
) -> None:
    safe_payload = _sanitize_mapping(payload)
    await publish_event(
        event_bus,
        organization_id=organization_id,
        session_id=session_id,
        event_type=event_type,
        request_context=request_context,
        payload=safe_payload,
    )


def _sanitize_mapping(payload: dict[str, object]) -> dict[str, object]:
    return {
        key: _sanitize_value(value)
        for key, value in payload.items()
        if not any(token in key.lower() for token in ("secret", "token", "cookie", "password"))
    }


def _sanitize_value(value: object) -> object:
    if isinstance(value, dict):
        return _sanitize_mapping({str(key): child for key, child in value.items()})
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value
