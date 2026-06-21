"""Graceful shutdown helpers."""

import asyncio

from live_demo_agent_runtime.sessions.voice_session_manager import VoiceSessionManager


async def shutdown_voice_sessions(manager: VoiceSessionManager, timeout_seconds: int) -> None:
    try:
        await asyncio.wait_for(manager.shutdown(), timeout=timeout_seconds)
    except TimeoutError:
        await manager.shutdown()
