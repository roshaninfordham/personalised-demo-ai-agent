"""Event names emitted by the voice runtime."""

VOICE_SESSION_CREATED = "agent.voice_session.created"
VOICE_SESSION_STARTING = "agent.voice_session.starting"
VOICE_SESSION_WAITING_FOR_CLIENT = "agent.voice_session.waiting_for_client"
VOICE_SESSION_CONNECTED = "agent.voice_session.connected"
VOICE_SESSION_ACTIVE = "agent.voice_session.active"
VOICE_SESSION_STOPPING = "agent.voice_session.stopping"
VOICE_SESSION_STOPPED = "agent.voice_session.stopped"
VOICE_SESSION_FAILED = "agent.voice_session.failed"

AGENT_TURN_STARTED = "agent.turn.started"
AGENT_TURN_COMPLETED = "agent.turn.completed"
AGENT_INTERRUPTED = "agent.interrupted"

TRANSCRIPT_PARTIAL = "transcript.partial"
TRANSCRIPT_FINAL = "transcript.final"
TRANSCRIPT_INTERRUPTED = "transcript.interrupted"

VOICE_LATENCY_UPDATED = "voice.latency.updated"
VOICE_PROVIDER_HEALTH = "voice.provider.health"
VOICE_ERROR = "voice.error"
