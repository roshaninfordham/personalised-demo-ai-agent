"""Publish bounded latency updates."""

from uuid import UUID

from live_demo_agent_runtime.events import event_types
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.metrics.latency import VoiceLatencyTracker


async def publish_latency_snapshot(
    *,
    publisher: EventPublisher,
    tracker: VoiceLatencyTracker,
    organization_id: UUID,
    demo_session_id: UUID,
    trace_id: str,
) -> None:
    payload = tracker.snapshot()
    if not payload:
        return
    await publisher.publish(
        organization_id=organization_id,
        demo_session_id=demo_session_id,
        event_type=event_types.VOICE_LATENCY_UPDATED,
        trace_id=trace_id,
        payload=payload,
    )
