"""Resource cleanup helpers."""

from __future__ import annotations

from uuid import UUID

from live_demo_api.clients.agent_runtime_client import AgentRuntimeClient
from live_demo_api.clients.browser_runtime_client import BrowserRuntimeClient
from live_demo_api.clients.learner_worker_client import LearnerWorkerClient
from live_demo_api.orchestration.orchestration_types import SessionResource


class ResourceCleanup:
    def __init__(
        self,
        *,
        browser_client: BrowserRuntimeClient,
        agent_client: AgentRuntimeClient,
        learner_client: LearnerWorkerClient,
    ) -> None:
        self._browser = browser_client
        self._agent = agent_client
        self._learner = learner_client

    async def release(self, resource: SessionResource, *, trace_id: str) -> bool:
        if resource.resource_type == "voice_session":
            return await self._agent.stop_voice_session(
                voice_session_id=_uuid(resource.resource_id), trace_id=trace_id
            )
        if resource.resource_type == "browser_session":
            return await self._browser.close_session(
                browser_session_id=_uuid(resource.resource_id), trace_id=trace_id
            )
        if resource.resource_type == "learner_run":
            return await self._learner.detach_or_cancel_run(
                learner_run_id=_uuid(resource.resource_id), trace_id=trace_id
            )
        return True


def _uuid(value: str) -> UUID:
    return UUID(value)
