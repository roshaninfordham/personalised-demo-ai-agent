"""Typed event publisher protocol."""

from collections.abc import Mapping
from typing import Protocol
from uuid import UUID


class EventPublisher(Protocol):
    async def publish(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        event_type: str,
        trace_id: str,
        payload: Mapping[str, object],
    ) -> str: ...
