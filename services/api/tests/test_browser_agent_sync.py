from __future__ import annotations

from uuid import uuid4

import pytest

from live_demo_api.orchestration.browser_agent_sync import BrowserAgentSynchronizer


class MemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> bytes | None:
        value = self.values.get(key)
        return value.encode("utf-8") if value is not None else None

    async def setex(self, key: str, _ttl: int, value: str) -> bool:
        self.values[key] = value
        return True


async def test_sync_queues_only_one_pending_action() -> None:
    sync = BrowserAgentSynchronizer(MemoryRedis())  # type: ignore[arg-type]
    session_id = uuid4()

    state = await sync.queue_action(
        session_id=session_id,
        turn_id=uuid4(),
        action_id="act_1",
        command_id=uuid4(),
    )

    assert state.browser_action_state == "queued"
    with pytest.raises(ValueError, match="action_already_pending"):
        await sync.queue_action(
            session_id=session_id,
            turn_id=uuid4(),
            action_id="act_2",
            command_id=uuid4(),
        )


async def test_interruption_cancels_not_yet_started_action() -> None:
    sync = BrowserAgentSynchronizer(MemoryRedis())  # type: ignore[arg-type]
    session_id = uuid4()
    await sync.queue_action(
        session_id=session_id,
        turn_id=uuid4(),
        action_id="act_1",
        command_id=uuid4(),
    )

    interrupted = await sync.mark_interrupted(session_id)

    assert interrupted.speech_state == "interrupted"
    assert interrupted.browser_action_state == "idle"
    assert interrupted.pending_action_id is None
