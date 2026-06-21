"""Safe exploration wrapper around the browser runtime client."""

from __future__ import annotations

from live_demo_learner_worker.browser.browser_runtime_client import (
    BrowserActionResult,
    BrowserRuntimeClient,
    SafeAction,
)
from live_demo_learner_worker.exploration.exploration_policy import ExplorationPolicy


class SafeExplorationClient:
    def __init__(self, browser_client: BrowserRuntimeClient, policy: ExplorationPolicy) -> None:
        self._browser_client = browser_client
        self._policy = policy

    async def execute_if_allowed(self, action: SafeAction) -> BrowserActionResult | None:
        if not self._policy.is_allowed(action):
            return None
        return await self._browser_client.execute_action(action)
