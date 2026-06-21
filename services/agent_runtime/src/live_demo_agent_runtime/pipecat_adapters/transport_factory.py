"""Transport provider factory."""

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ConfigurationError
from live_demo_agent_runtime.transports.base import RealtimeVoiceTransport
from live_demo_agent_runtime.transports.custom_transport import CustomTransportProvider
from live_demo_agent_runtime.transports.daily_transport import DailyTransportProvider
from live_demo_agent_runtime.transports.small_webrtc_transport import SmallWebRTCTransportProvider


class TransportFactory:
    def __init__(self, settings: AgentRuntimeSettings) -> None:
        self._settings = settings

    def create_transport_provider(self, provider_name: str | None = None) -> RealtimeVoiceTransport:
        selected = provider_name or self._settings.transport_provider
        if selected == "small_webrtc":
            return SmallWebRTCTransportProvider(self._settings)
        if selected == "daily":
            return DailyTransportProvider(self._settings)
        if selected == "custom":
            return CustomTransportProvider()
        raise ConfigurationError("Invalid transport provider.", {"provider_name": selected})
