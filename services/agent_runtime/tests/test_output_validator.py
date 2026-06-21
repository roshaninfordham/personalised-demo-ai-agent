import json

import pytest

from live_demo_agent_runtime.agent_brain.output_validator import (
    AgentOutputValidationError,
    AgentOutputValidator,
)

from .agent_brain_helpers import realtime_context, safe_action


def _decision(**overrides: object) -> str:
    payload: dict[str, object] = {
        "spoken_response": "From what I can verify on screen, this is the dashboard.",
        "browser_action": None,
        "memory_updates": [],
        "confidence": 0.8,
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_valid_output_accepted() -> None:
    decision = AgentOutputValidator().validate(
        _decision(
            browser_action={
                "action_id": "act_click_dashboard",
                "tool_name": "click_element",
                "reason": "Visible dashboard action.",
            }
        ),
        realtime_context(),
    )
    assert decision.browser_action is not None


def test_invalid_json_rejected() -> None:
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate("not-json", realtime_context())


def test_missing_required_and_extra_field_rejected() -> None:
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(json.dumps({"spoken_response": "x"}), realtime_context())
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(_decision(extra=True), realtime_context())


def test_raw_selector_and_javascript_rejected() -> None:
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(
            _decision(
                browser_action={
                    "action_id": "act_click_dashboard",
                    "tool_name": "click_element",
                    "reason": "Use document.querySelector('#x')",
                }
            ),
            realtime_context(),
        )


def test_unknown_action_and_tool_mismatch_rejected() -> None:
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(
            _decision(
                browser_action={
                    "action_id": "missing",
                    "tool_name": "click_element",
                    "reason": "Unknown.",
                }
            ),
            realtime_context(),
        )
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(
            _decision(
                browser_action={
                    "action_id": "act_click_dashboard",
                    "tool_name": "scroll",
                    "reason": "Mismatch.",
                }
            ),
            realtime_context(),
        )


def test_memory_update_without_evidence_and_bad_confidence_rejected() -> None:
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(
            _decision(
                memory_updates=[
                    {
                        "type": "feature_interest",
                        "content": "Metrics",
                        "confidence": 0.8,
                        "evidence": {
                            "transcript_event_ids": [],
                            "screen_ids": [],
                            "action_ids": [],
                        },
                    }
                ]
            ),
            realtime_context(),
        )
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(_decision(confidence=2), realtime_context())


def test_unsupported_claim_rejected_but_grounded_claim_allowed() -> None:
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(
            _decision(spoken_response="This integrates with Salesforce."),
            realtime_context(product_summary=None),
        )
    context = realtime_context(
        product_summary=None,
        screen=None,
        actions=(safe_action(),),
    )
    assert AgentOutputValidator().validate(
        _decision(spoken_response="The dashboard is visible on screen."),
        context,
    )
