import asyncio
import logging

from live_demo_learner_worker.config import get_settings
from live_demo_learner_worker.health import health_check

LOGGER = logging.getLogger(__name__)


async def run_worker() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    LOGGER.info(
        "Learner worker skeleton started. Product summarization is not implemented in Phase 1."
    )
    LOGGER.debug("Learner worker health: %s", health_check())

    stop_event = asyncio.Event()
    await stop_event.wait()


def main() -> None:
    asyncio.run(run_worker())
