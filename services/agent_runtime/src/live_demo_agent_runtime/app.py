"""FastAPI application factory for the agent runtime."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from live_demo_agent_runtime.config import get_settings
from live_demo_agent_runtime.db.session import (
    dispose_database_engine,
    get_async_engine,
    get_sessionmaker,
)
from live_demo_agent_runtime.errors import AgentRuntimeError
from live_demo_agent_runtime.events.redis_event_publisher import RedisEventPublisher
from live_demo_agent_runtime.logging_config import configure_logging
from live_demo_agent_runtime.pipecat_adapters.transport_factory import TransportFactory
from live_demo_agent_runtime.redis.redis_client import close_redis_client, get_redis_client
from live_demo_agent_runtime.routes.health import router as health_router
from live_demo_agent_runtime.routes.voice_sessions import router as voice_sessions_router
from live_demo_agent_runtime.sessions.voice_session_manager import VoiceSessionManager
from live_demo_agent_runtime.stt import SttProviderRegistry
from live_demo_agent_runtime.transcripts.transcript_event_publisher import TranscriptEventPublisher
from live_demo_agent_runtime.transcripts.transcript_repository import TranscriptRepository
from live_demo_agent_runtime.transcripts.transcript_sink import TranscriptSink
from live_demo_agent_runtime.tts import TtsProviderRegistry


def _error_envelope(
    *,
    code: str,
    message: str,
    request_id: str,
    trace_id: str,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "trace_id": trace_id,
            "details": details or {},
        }
    }


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    get_async_engine()
    sessionmaker = get_sessionmaker()
    redis_client = get_redis_client()
    event_publisher = RedisEventPublisher(redis_client, settings)
    transcript_event_publisher = TranscriptEventPublisher(event_publisher)
    transcript_sink = TranscriptSink(
        sessionmaker=sessionmaker,
        repository=TranscriptRepository(),
        publisher=transcript_event_publisher,
    )
    transport_provider = TransportFactory(settings).create_transport_provider(
        settings.transport_provider
    )
    manager = VoiceSessionManager(
        settings=settings,
        event_publisher=event_publisher,
        transport=transport_provider,
        transcript_sink=transcript_sink,
    )
    app.state.settings = settings
    app.state.event_publisher = event_publisher
    app.state.transcript_sink = transcript_sink
    app.state.transport_provider = transport_provider
    app.state.stt_registry = SttProviderRegistry(settings)
    app.state.tts_registry = TtsProviderRegistry(settings)
    app.state.voice_session_manager = manager
    try:
        yield
    finally:
        await manager.shutdown()
        await cast(SttProviderRegistry, app.state.stt_registry).close()
        await cast(TtsProviderRegistry, app.state.tts_registry).close()
        await close_redis_client()
        await dispose_database_engine()


def create_app() -> FastAPI:
    app = FastAPI(title="Live Demo Agent Runtime", lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(voice_sessions_router)

    @app.middleware("http")
    async def request_id_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = (request.headers.get("x-request-id") or "req-local")[:128]
        trace_id = (request.headers.get("x-trace-id") or request_id)[:128]
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        return response

    @app.exception_handler(AgentRuntimeError)
    async def app_error_handler(request: Request, exc: AgentRuntimeError) -> JSONResponse:
        request_id = str(getattr(request.state, "request_id", ""))
        trace_id = str(getattr(request.state, "trace_id", request_id))
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_envelope(
                code=exc.code,
                message=exc.safe_message,
                request_id=request_id,
                trace_id=trace_id,
                details=exc.details,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        del exc
        request_id = str(getattr(request.state, "request_id", ""))
        trace_id = str(getattr(request.state, "trace_id", request_id))
        return JSONResponse(
            status_code=500,
            content=_error_envelope(
                code="agent_runtime_internal_error",
                message="Agent runtime error.",
                request_id=request_id,
                trace_id=trace_id,
            ),
        )

    return app
