from live_demo_agent_runtime.agent_brain.json_repair import strip_json_code_fence


def test_json_repair_strips_code_fence_only() -> None:
    raw = '```json\n{"spoken_response":"ok"}\n```'
    assert strip_json_code_fence(raw) == '{"spoken_response":"ok"}'
