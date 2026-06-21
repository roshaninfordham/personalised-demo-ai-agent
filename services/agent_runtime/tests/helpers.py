from typing import Any, cast

from live_demo_agent_runtime.config import AgentRuntimeSettings


def test_settings(**kwargs: object) -> AgentRuntimeSettings:
    settings_factory = cast(Any, AgentRuntimeSettings)
    return cast(AgentRuntimeSettings, settings_factory(**kwargs, _env_file=None))
