"""Prompt and LLM request construction for the host agent."""

from pathlib import Path

from live_demo_agent_runtime.agent_brain.agent_output_schema import AGENT_OUTPUT_SCHEMA
from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.context.context_packager import render_context_json
from live_demo_agent_runtime.context.context_types import RealtimeAgentContext
from live_demo_agent_runtime.prompts import prompt_path
from live_demo_backend_common.ai.types import ChatMessage, MessageRole, TextGenerationRequest


def load_host_system_prompt() -> str:
    return prompt_path("host_agent_system.md").read_text(encoding="utf-8")


def load_host_developer_prompt() -> str:
    path: Path = prompt_path("host_agent_developer.md")
    return path.read_text(encoding="utf-8")


def build_host_agent_request(
    *,
    context: RealtimeAgentContext,
    settings: AgentRuntimeSettings,
    request_id: str,
    trace_id: str,
    fake_response: str | None = None,
) -> TextGenerationRequest:
    metadata = {
        "purpose": settings.agent_brain_provider_purpose,
        "request_id": request_id,
        "trace_id": trace_id,
        "session_id": str(context.demo_session_id),
    }
    if fake_response is not None:
        metadata["fake_response"] = fake_response
    return TextGenerationRequest(
        messages=[
            ChatMessage(role=MessageRole.system, content=load_host_system_prompt()),
            ChatMessage(
                role=MessageRole.system,
                content=load_host_developer_prompt() + "\n" + render_context_json(context),
            ),
            ChatMessage(role=MessageRole.user, content=context.user_utterance),
        ],
        temperature=settings.agent_brain_temperature,
        top_p=settings.agent_brain_top_p,
        max_output_tokens=settings.agent_brain_max_output_tokens,
        response_format="json_schema" if settings.agent_brain_enable_json_schema else "json_object",
        json_schema={"name": "agent_decision", "schema": AGENT_OUTPUT_SCHEMA}
        if settings.agent_brain_enable_json_schema
        else None,
        timeout_ms=settings.agent_brain_timeout_ms,
        metadata=metadata,
    )
