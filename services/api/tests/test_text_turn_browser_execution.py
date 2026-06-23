from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from live_demo_api.routers.demo_sessions import _execute_browser_action_if_possible
from live_demo_api.security import RequestContext


class FakeStore:
    def __init__(self, browser_session_id: UUID | None) -> None:
        self._browser_session_id = browser_session_id

    async def get_browser_status(self, session_id: UUID) -> dict[str, str] | None:
        _ = session_id
        if self._browser_session_id is None:
            return None
        return {"browser_session_id": str(self._browser_session_id)}


@pytest.mark.asyncio
async def test_browser_action_execution_rejects_unsupported_action_without_fake_success() -> None:
    result = await _execute_browser_action_if_possible(
        store=cast(Any, FakeStore(uuid4())),
        session_id=uuid4(),
        action={"action_type": "type_into_element", "action_id": "act_type_password"},
        request_context=RequestContext(request_id="req", trace_id="trace"),
    )

    assert result.success is False
    assert result.error_code == "unsupported_action_type"


@pytest.mark.asyncio
async def test_browser_action_execution_requires_active_browser_session() -> None:
    result = await _execute_browser_action_if_possible(
        store=cast(Any, FakeStore(None)),
        session_id=uuid4(),
        action={
            "action_type": "click_element",
            "action_id": "act_click_signup",
            "element_id": "el_signup",
        },
        request_context=RequestContext(request_id="req", trace_id="trace"),
    )

    assert result.success is False
    assert result.error_code == "browser_session_unavailable"


@pytest.mark.asyncio
async def test_browser_action_execution_surfaces_browser_runtime_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_action(self: object, **kwargs: object) -> dict[str, object]:
        _ = self, kwargs
        return {
            "success": False,
            "error_code": "stale_element",
            "error_message": "Element changed before click.",
        }

    monkeypatch.setattr(
        "live_demo_api.routers.demo_sessions.BrowserRuntimeClient.execute_action",
        fail_action,
    )
    result = await _execute_browser_action_if_possible(
        store=cast(Any, FakeStore(uuid4())),
        session_id=uuid4(),
        action={
            "action_type": "click_element",
            "action_id": "act_click_signup",
            "element_id": "el_signup",
        },
        request_context=RequestContext(request_id="req", trace_id="trace"),
    )

    assert result.success is False
    assert result.error_code == "stale_element"
    assert result.error_message == "Element changed before click."
