# TTS/STT Failures

## Symptom

Fake STT/TTS works but real voice does not, first audio is slow, partial transcripts never appear, or local model startup fails.

## Likely Causes

- Whisper model path missing.
- whisper.cpp binary path missing.
- Kokoro service down.
- Piper model path wrong.
- Cartesia key missing.
- Local CPU/GPU is too slow.
- Provider timeout too low.

## Quick Checks

```bash
docker compose logs tts-service --tail=200
docker compose logs agent-runtime --tail=200
grep AI_STT_ .env
grep AI_TTS_ .env
```

## Logs and Metrics

Check:

- `voice.stt.final`;
- `voice.tts.first_audio`;
- `stt_unavailable`;
- `tts_unavailable`;
- STT/TTS latency dashboards.

## Fix

- Use fake providers first.
- Verify binary and model paths.
- Start `tts-local` profile for Kokoro mode.
- Use cloud STT/TTS for smoother demos if local hardware is weak.

## Prevention

Do not make real voice providers part of default CI. Keep deterministic text-turn fallback for interviews.
