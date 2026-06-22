# Slow Local Hardware

## Symptom

Docker feels slow, first audio takes several seconds, browser actions lag, or local models consume most CPU/memory.

## Likely Causes

- Ollama model too large.
- Browser runtime plus observability stack exceeds laptop resources.
- Docker memory is too low.
- Local STT/TTS runs on CPU.
- Too many concurrent browser sessions.

## Quick Checks

```bash
docker stats
docker compose ps
docker compose logs browser-runtime --tail=100
```

## Logs and Metrics

Check:

- latency budget dashboard;
- browser action latency;
- first-audio latency;
- container memory usage.

## Fix

Recommended lower-resource mode:

```env
AI_TEXT_PROVIDER=fake
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
```

Run only core services:

```bash
make up web api browser-runtime agent-runtime postgres redis minio
```

Other options:

- disable observability profile;
- disable Ollama;
- reduce `BROWSER_MAX_CONCURRENT_SESSIONS`;
- increase Docker memory;
- close other applications.

## Prevention

Use fake providers for local deterministic tests and hosted providers for polished demos when laptop resources are weak.
