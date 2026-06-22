"""Product learner worker entrypoint."""

from __future__ import annotations

import asyncio
import logging
import signal
from contextlib import suppress

from redis.asyncio import Redis

from live_demo_learner_worker.config import get_settings
from live_demo_learner_worker.dependencies import build_dependencies
from live_demo_learner_worker.logging_config import configure_logging
from live_demo_learner_worker.observability.setup import setup_observability
from live_demo_learner_worker.worker.product_learner_worker import ProductLearnerWorker

LOGGER = logging.getLogger(__name__)


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    setup_observability(settings)
    redis: Redis[bytes] = Redis.from_url(settings.redis_url)
    dependencies = build_dependencies(settings, redis)
    worker = ProductLearnerWorker(dependencies)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    LOGGER.info("learner_worker.starting", extra={"settings": settings.safe_log_dict()})
    worker_task = asyncio.create_task(worker.run_forever())
    stop_task = asyncio.create_task(stop_event.wait())
    try:
        done, _ = await asyncio.wait(
            {worker_task, stop_task}, return_when=asyncio.FIRST_COMPLETED
        )
        if worker_task in done:
            worker_task.result()
            stop_event.set()
        await worker.stop()
        if not worker_task.done():
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task
    finally:
        stop_task.cancel()
        with suppress(asyncio.CancelledError):
            await stop_task
        await redis.close()
        await dependencies.db_engine.dispose()
    LOGGER.info("learner_worker.stopped")


def main() -> None:
    asyncio.run(run_worker())
