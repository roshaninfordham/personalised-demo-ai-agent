"""Join config response objects."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VoiceJoinConfig:
    transport_provider: str
    voice_session_id: UUID
    expires_at: datetime
    status: str
    signaling_url: str | None = None
    offer_required: bool = True
    ice_servers: list[dict[str, object]] = field(default_factory=list)
    room_url: str | None = None
    token: str | None = None

    def to_response(self) -> dict[str, object]:
        response: dict[str, object] = {
            "transport_provider": self.transport_provider,
            "voice_session_id": str(self.voice_session_id),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
            "offer_required": self.offer_required,
            "ice_servers": self.ice_servers,
        }
        if self.signaling_url is not None:
            response["signaling_url"] = self.signaling_url
        if self.room_url is not None:
            response["room_url"] = self.room_url
        if self.token is not None:
            response["token"] = self.token
        return response
