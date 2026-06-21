"""Browser runtime client boundary."""

from typing import Protocol
from uuid import UUID

import httpx

ACTION_ENDPOINTS: dict[str, str] = {
    "read_current_screen": "read_current_screen",
    "highlight_element": "highlight_element",
    "click_element": "click_element",
    "type_demo_text": "type_into_element",
    "scroll": "scroll",
    "go_back": "go_back",
}


class BrowserToolClient(Protocol):
    async def execute_action(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        action_id: str,
        tool_name: str,
        arguments: dict[str, object],
        trace_id: str,
    ) -> dict[str, object]: ...


class BrowserRuntimeToolClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_ms: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_ms / 1000)
        self._client = client or httpx.AsyncClient(timeout=self._timeout)
        self._owns_client = client is None

    async def execute_action(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        action_id: str,
        tool_name: str,
        arguments: dict[str, object],
        trace_id: str,
    ) -> dict[str, object]:
        del organization_id
        endpoint = ACTION_ENDPOINTS.get(tool_name)
        if endpoint is None:
            return {"success": False, "error_code": "unsupported_browser_tool"}
        browser_session_id = arguments.get("browser_session_id")
        if not isinstance(browser_session_id, str) or not browser_session_id:
            return {"success": False, "error_code": "missing_browser_session_id"}
        body = {
            "action_id": action_id,
            "demo_session_id": str(demo_session_id),
            "trace_id": trace_id,
            **{key: value for key, value in arguments.items() if key != "browser_session_id"},
        }
        response = await self._client.post(
            f"{self._base_url}/internal/browser/v1/sessions/"
            f"{browser_session_id}/actions/{endpoint}",
            json=body,
            headers={"X-Trace-ID": trace_id},
        )
        if response.is_error:
            return {
                "success": False,
                "error_code": "browser_runtime_unavailable",
                "status_code": response.status_code,
            }
        parsed = response.json()
        if not isinstance(parsed, dict):
            return {"success": False, "error_code": "invalid_browser_response"}
        return {"success": parsed.get("success") is not False, **parsed}

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


class FakeBrowserToolClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict[str, object]] = []

    async def execute_action(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        action_id: str,
        tool_name: str,
        arguments: dict[str, object],
        trace_id: str,
    ) -> dict[str, object]:
        call: dict[str, object] = {
            "organization_id": str(organization_id),
            "demo_session_id": str(demo_session_id),
            "action_id": action_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "trace_id": trace_id,
        }
        self.calls.append(call)
        if self.fail:
            return {"success": False, "error_code": "browser_action_failed"}
        return {"success": True, "action_id": action_id, "tool_name": tool_name}
