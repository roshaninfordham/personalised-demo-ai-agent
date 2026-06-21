import uvicorn

from live_demo_agent_runtime.app import create_app
from live_demo_agent_runtime.config import get_settings

app = create_app()


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "live_demo_agent_runtime.main:app",
        host=settings.agent_runtime_host,
        port=settings.agent_runtime_port,
    )
