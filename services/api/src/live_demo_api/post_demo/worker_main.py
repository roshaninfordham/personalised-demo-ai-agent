"""Post-demo worker process entrypoint.

Phase 16 packages the post-demo worker as a separately deployable container.
The queue consumer can be wired behind this process without changing the image
or Kubernetes manifests.
"""

from __future__ import annotations

import asyncio
import logging
import signal

from live_demo_api.config import get_settings

LOGGER = logging.getLogger("live_demo_api.post_demo.worker")


async def run_worker() -> None:
    settings = get_settings()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    LOGGER.info(
        "Post-demo worker started.",
        extra={
            "stream": settings.post_demo_job_stream,
            "consumer_group": settings.post_demo_consumer_group,
        },
    )
    await stop_event.wait()
    LOGGER.info("Post-demo worker stopping.")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
