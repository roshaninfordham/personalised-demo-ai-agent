"""Pipeline processor that runs the realtime agent on final transcripts."""

from uuid import UUID

from live_demo_agent_runtime.agent_brain.host_agent_runner import (
    AgentTurnRequest,
    AgentTurnResult,
    HostAgentRunner,
)
from live_demo_agent_runtime.transcripts.transcript_buffer import TranscriptWriteItem


class RealtimeAgentProcessor:
    def __init__(self, runner: HostAgentRunner) -> None:
        self._runner = runner

    async def process_transcript(
        self,
        item: TranscriptWriteItem,
        *,
        product_id: UUID,
        trace_id: str,
        fake_llm_response: str | None = None,
    ) -> AgentTurnResult | None:
        if item.speaker != "user" or item.chunk_type != "final" or item.turn_id is None:
            return None
        return await self._runner.run_turn(
            AgentTurnRequest(
                organization_id=item.organization_id,
                demo_session_id=item.demo_session_id,
                product_id=product_id,
                user_utterance=item.text,
                user_transcript_event_id=item.transcript_event_id,
                active_turn_id=item.turn_id,
                trace_id=trace_id,
                fake_llm_response=fake_llm_response,
            )
        )
