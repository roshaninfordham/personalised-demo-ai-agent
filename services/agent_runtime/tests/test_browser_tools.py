import httpx

from live_demo_agent_runtime.context.context_types import KnowledgeFactContext
from live_demo_agent_runtime.tools.browser_tool_client import BrowserRuntimeToolClient
from live_demo_agent_runtime.tools.browser_tool_definitions import BROWSER_TOOLS, tool_names
from live_demo_agent_runtime.tools.knowledge_tool import search_product_knowledge

from .agent_brain_helpers import DEMO_SESSION_ID, ORG_ID


def test_browser_tool_set_contains_required_tools() -> None:
    names = tool_names()
    assert {
        "read_current_screen",
        "highlight_element",
        "click_element",
        "type_demo_text",
        "scroll",
        "go_back",
        "search_product_knowledge",
        "save_lead_insight",
    } <= names
    assert all(tool.risk for tool in BROWSER_TOOLS)


async def test_search_product_knowledge_is_bounded() -> None:
    result = await search_product_knowledge(
        [
            KnowledgeFactContext("low", "one", 0.1, "test"),
            KnowledgeFactContext("high", "dashboard fact", 0.9, "test"),
        ],
        top_k=1,
        min_score=0.5,
    )
    assert [fact.fact_id for fact in result] == ["high"]


async def test_browser_runtime_tool_client_requires_browser_session_and_maps_endpoint() -> None:
    captured: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.append(str(request.url))
        return httpx.Response(200, json={"success": True, "observed": True})

    client = BrowserRuntimeToolClient(
        base_url="http://browser-runtime",
        timeout_ms=1000,
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    missing = await client.execute_action(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
        action_id="act",
        tool_name="click_element",
        arguments={},
        trace_id="trace",
    )
    assert missing["success"] is False
    result = await client.execute_action(
        organization_id=ORG_ID,
        demo_session_id=DEMO_SESSION_ID,
        action_id="act",
        tool_name="type_demo_text",
        arguments={"browser_session_id": "browser-1", "text": "Demo Metric"},
        trace_id="trace",
    )
    await client.close()
    assert result["success"] is True
    assert captured == [
        "http://browser-runtime/internal/browser/v1/sessions/browser-1/actions/type_into_element"
    ]
