"""Pipeline wrapper around browser tool routing."""

from live_demo_agent_runtime.tools.browser_tool_results import ToolRouteRequest, ToolRouteResult
from live_demo_agent_runtime.tools.browser_tool_router import BrowserToolRouter


class ToolRouterProcessor:
    def __init__(self, tool_router: BrowserToolRouter) -> None:
        self._tool_router = tool_router

    async def process(self, request: ToolRouteRequest) -> ToolRouteResult:
        return await self._tool_router.route(request)
