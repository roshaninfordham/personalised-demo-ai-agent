from uuid import uuid4

import pytest

from live_demo_agent_runtime.errors import VoiceSessionLimitError
from live_demo_agent_runtime.events.redis_event_publisher import InMemoryEventPublisher
from live_demo_agent_runtime.pipecat_adapters.transport_factory import TransportFactory
from live_demo_agent_runtime.sessions.session_state import VoiceSessionStatus
from live_demo_agent_runtime.sessions.voice_session_manager import VoiceSessionManager

from .helpers import test_settings


def _manager(max_active: int = 5) -> VoiceSessionManager:
    settings = test_settings(voice_session_max_active=max_active)
    return VoiceSessionManager(
        settings=settings,
        event_publisher=InMemoryEventPublisher(),
        transport=TransportFactory(settings).create_transport_provider("small_webrtc"),
        transcript_sink=None,
    )


async def test_create_session_succeeds() -> None:
    manager = _manager()
    session, join_config = await manager.create_session(
        organization_id=uuid4(),
        demo_session_id=uuid4(),
        product_id=uuid4(),
        transport_provider="small_webrtc",
        trace_id="trace",
    )
    assert session.status == VoiceSessionStatus.WAITING_FOR_CLIENT
    assert join_config.transport_provider == "small_webrtc"


async def test_duplicate_active_demo_session_is_idempotent() -> None:
    manager = _manager()
    demo_session_id = uuid4()
    first, _ = await manager.create_session(
        organization_id=uuid4(),
        demo_session_id=demo_session_id,
        product_id=uuid4(),
        transport_provider="small_webrtc",
        trace_id="trace",
    )
    second, _ = await manager.create_session(
        organization_id=uuid4(),
        demo_session_id=demo_session_id,
        product_id=uuid4(),
        transport_provider="small_webrtc",
        trace_id="trace",
    )
    assert first.voice_session_id == second.voice_session_id


async def test_max_active_sessions_enforced() -> None:
    manager = _manager(max_active=1)
    await manager.create_session(
        organization_id=uuid4(),
        demo_session_id=uuid4(),
        product_id=uuid4(),
        transport_provider="small_webrtc",
        trace_id="trace",
    )
    with pytest.raises(VoiceSessionLimitError):
        await manager.create_session(
            organization_id=uuid4(),
            demo_session_id=uuid4(),
            product_id=uuid4(),
            transport_provider="small_webrtc",
            trace_id="trace",
        )


async def test_stop_session_is_idempotent() -> None:
    manager = _manager()
    session, _ = await manager.create_session(
        organization_id=uuid4(),
        demo_session_id=uuid4(),
        product_id=uuid4(),
        transport_provider="small_webrtc",
        trace_id="trace",
    )
    stopped = await manager.stop_session(session.voice_session_id)
    assert stopped.status == VoiceSessionStatus.STOPPED
    stopped_again = await manager.stop_session(session.voice_session_id)
    assert stopped_again.status == VoiceSessionStatus.STOPPED
