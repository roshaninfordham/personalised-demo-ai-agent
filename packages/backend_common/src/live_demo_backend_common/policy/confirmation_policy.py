from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ConfirmationToken:
    token: str
    session_id: str
    action_id: str
    actor_id: str
    risk_level: str
    expires_at: datetime


class InMemoryConfirmationStore:
    def __init__(self) -> None:
        self._tokens: dict[str, ConfirmationToken] = {}

    def create(
        self,
        *,
        session_id: str,
        action_id: str,
        actor_id: str,
        risk_level: str,
        ttl_seconds: int = 120,
    ) -> ConfirmationToken:
        token = ConfirmationToken(
            token=str(uuid4()),
            session_id=session_id,
            action_id=action_id,
            actor_id=actor_id,
            risk_level=risk_level,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        )
        self._tokens[token.token] = token
        return token

    def validate(
        self,
        *,
        token: str,
        session_id: str,
        action_id: str,
        actor_id: str,
        risk_level: str,
    ) -> bool:
        stored = self._tokens.get(token)
        return (
            stored is not None
            and stored.expires_at >= datetime.now(UTC)
            and stored.session_id == session_id
            and stored.action_id == action_id
            and stored.actor_id == actor_id
            and stored.risk_level == risk_level
        )
