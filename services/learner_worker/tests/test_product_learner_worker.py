from __future__ import annotations

from live_demo_learner_worker.worker.shutdown import ShutdownState


def test_shutdown_state_is_idempotent() -> None:
    state = ShutdownState()
    state.request_stop()
    state.request_stop()
    assert state.draining
