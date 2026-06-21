from live_demo_agent_runtime.context.context_packager import render_context_json

from .agent_brain_helpers import realtime_context


def test_context_packager_is_stable_and_excludes_html() -> None:
    context = realtime_context()
    assert render_context_json(context) == render_context_json(context)
    assert "<html" not in render_context_json(context).lower()
