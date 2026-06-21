from datetime import UTC, datetime
from uuid import uuid4

import pytest

from live_demo_agent_runtime.errors import ConfigurationError, ProviderCapabilityError
from live_demo_agent_runtime.pipecat_adapters.transport_factory import TransportFactory

from .helpers import test_settings


def test_small_webrtc_selected_by_config() -> None:
    provider = TransportFactory(test_settings()).create_transport_provider("small_webrtc")
    assert provider.provider_name == "small_webrtc"


async def test_daily_missing_key_returns_not_configured() -> None:
    provider = TransportFactory(test_settings()).create_transport_provider("daily")
    with pytest.raises(ProviderCapabilityError):
        await provider.create_session(
            voice_session_id=uuid4(),
            organization_id=uuid4(),
            demo_session_id=uuid4(),
            product_id=uuid4(),
            expires_at=datetime.now(UTC),
        )


def test_invalid_transport_provider_raises() -> None:
    with pytest.raises(ConfigurationError):
        TransportFactory(test_settings()).create_transport_provider("bad")
