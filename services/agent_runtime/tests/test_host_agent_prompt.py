from live_demo_agent_runtime.agent_brain.host_agent import load_host_system_prompt


def test_host_agent_prompt_contains_safety_and_grounding_policy() -> None:
    prompt = load_host_system_prompt().lower()
    assert "grounded" in prompt
    assert "raw selectors" in prompt
    assert "javascript" in prompt
    assert "safe action_id" in prompt
    assert "1-3 sentences" in prompt
    assert "uncertain" in prompt
