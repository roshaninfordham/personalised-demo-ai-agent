"""Safe browser tool definitions exposed to the agent."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BrowserToolDefinition:
    name: str
    description: str
    risk: str


BROWSER_TOOLS: tuple[BrowserToolDefinition, ...] = (
    BrowserToolDefinition("read_current_screen", "Refresh current screen state.", "low"),
    BrowserToolDefinition("highlight_element", "Highlight a visible UI element.", "low"),
    BrowserToolDefinition("click_element", "Click a validated safe UI element.", "contextual"),
    BrowserToolDefinition("type_demo_text", "Type bounded synthetic demo text.", "contextual"),
    BrowserToolDefinition("scroll", "Scroll the page or panel.", "low"),
    BrowserToolDefinition("go_back", "Go back in browser history.", "medium"),
    BrowserToolDefinition("search_product_knowledge", "Search approved product knowledge.", "low"),
    BrowserToolDefinition(
        "save_lead_insight",
        "Persist a useful lead insight with evidence.",
        "low",
    ),
)


def tool_names() -> set[str]:
    return {tool.name for tool in BROWSER_TOOLS}
