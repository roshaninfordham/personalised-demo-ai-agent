# Microphone and WebRTC

## Symptom

The browser cannot access the microphone, no user audio reaches the agent, or the user cannot hear generated audio.

## Likely Causes

- Browser mic permission denied.
- No microphone device is available.
- `getUserMedia` is blocked on an insecure origin.
- SmallWebRTC signaling is unavailable.
- Daily is not configured.
- TTS provider is unavailable.
- Interruption detection is disabled or too insensitive.

## Quick Checks

```bash
curl -s $AGENT_RUNTIME_URL/healthz
curl -s $AGENT_RUNTIME_URL/readyz
docker compose logs agent-runtime --tail=200
```

For a session:

```bash
curl -s $API_URL/api/v1/demo-sessions/<session_id>/join-config
```

## Logs and Metrics

Check:

- frontend console logs;
- `voice_session_not_connected`;
- `tts_unavailable`;
- `stt_unavailable`;
- first-audio latency dashboard;
- `voice.interruption.detected` events.

## Fix

- Use `localhost` or HTTPS for browser mic access.
- Reset microphone permission in browser site settings.
- Switch to fake STT/TTS for local debugging.
- Verify `TRANSPORT_PROVIDER`.
- Verify provider keys only in backend env variables.

## Prevention

Keep scripted text-turn fallback available for interviews and CI. Test real mic access before a live demo.
