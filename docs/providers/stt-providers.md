# STT Providers

STT providers are configured through `AI_STT_*` variables.

Supported values:

- `fake`
- `whisper_local`
- `whisper_cpp`
- `deepgram`
- `custom`

Default:

```env
AI_STT_PROVIDER=fake
```

Use fake STT for deterministic local and CI runs. Use cloud STT for smoother realtime demos when local hardware is weak.

Troubleshooting:

```bash
grep AI_STT_ .env
docker compose logs agent-runtime --tail=200
```
