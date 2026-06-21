"""Static and configured safety context."""

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.context.context_types import SafetyRulesContext


def build_safety_rules(settings: AgentRuntimeSettings) -> SafetyRulesContext:
    never_click = tuple(
        item.strip() for item in settings.default_never_click.split(",") if item.strip()
    )
    blocked = tuple(
        sorted(
            {
                "Delete",
                "Billing",
                "Payment",
                "Invite",
                "Send",
                "Publish",
                "Upgrade",
                *never_click,
            }
        )
    )
    return SafetyRulesContext(
        never_click=never_click,
        blocked_actions=blocked,
        high_risk_requires_confirmation=True,
    )
