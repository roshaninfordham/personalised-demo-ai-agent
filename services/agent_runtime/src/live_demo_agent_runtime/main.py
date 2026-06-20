import asyncio
import logging

from live_demo_agent_runtime.config import get_settings
from live_demo_agent_runtime.health import health_check

LOGGER = logging.getLogger(__name__)


async def run_worker() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    LOGGER.info("Agent runtime skeleton started. Live voice loop is not implemented in Phase 1.")
    LOGGER.debug("Agent runtime health: %s", health_check())

    stop_event = asyncio.Event()
    await stop_event.wait()


def main() -> None:
    asyncio.run(run_worker())
