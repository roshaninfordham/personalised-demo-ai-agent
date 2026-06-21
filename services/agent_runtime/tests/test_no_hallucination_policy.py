import pytest

from live_demo_agent_runtime.agent_brain.output_validator import (
    AgentOutputValidationError,
    AgentOutputValidator,
)

from .agent_brain_helpers import realtime_context, screen_context


def test_agent_cannot_claim_salesforce_without_source() -> None:
    raw = (
        '{"spoken_response":"This integrates with Salesforce.",'
        '"browser_action":null,"memory_updates":[],"confidence":0.9}'
    )
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(raw, realtime_context(product_summary=None))


def test_agent_can_mention_visible_dashboard_with_source() -> None:
    raw = (
        '{"spoken_response":"From what I can verify on screen, the dashboard is visible.",'
        '"browser_action":null,"memory_updates":[],"confidence":0.8}'
    )
    assert AgentOutputValidator().validate(raw, realtime_context(screen=screen_context()))


def test_agent_says_cannot_verify_unsupported_feature() -> None:
    raw = (
        '{"spoken_response":"I cannot verify Salesforce integration from the current sources.",'
        '"browser_action":null,"memory_updates":[],"confidence":0.4}'
    )
    assert AgentOutputValidator().validate(raw, realtime_context(product_summary=None))
