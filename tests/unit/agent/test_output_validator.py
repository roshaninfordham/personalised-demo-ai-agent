import json

import pytest
from services.agent_runtime.tests.agent_brain_helpers import realtime_context

from live_demo_agent_runtime.agent_brain.output_validator import (
    AgentOutputValidationError,
    AgentOutputValidator,
)


def test_output_validator_blocks_raw_selector_action() -> None:
    with pytest.raises(AgentOutputValidationError):
        AgentOutputValidator().validate(
            json.dumps(
                {
                    "spoken_response": "I will avoid that unsafe selector.",
                    "browser_action": {
                        "action_id": "act_click_dashboard",
                        "tool_name": "click_element",
                        "reason": "document.querySelector('#delete')",
                    },
                    "memory_updates": [],
                    "confidence": 0.1,
                }
            ),
            realtime_context(),
        )
