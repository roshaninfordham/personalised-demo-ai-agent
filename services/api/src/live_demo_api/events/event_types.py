"""Event type constants from the shared contract."""

from live_demo_contracts.event import EventType

SUPPORTED_EVENT_TYPES = frozenset(event_type.value for event_type in EventType)
