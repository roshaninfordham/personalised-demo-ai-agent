# TTS Providers

TTS providers are configured through `AI_TTS_*` variables.

Supported values:

- `fake`
- `kokoro`
- `piper`
- `cartesia`
- `custom`

Default:

```env
AI_TTS_PROVIDER=fake
```

Local TTS profile:

```bash
docker compose --profile tts-local up --build
```

Cloud TTS requires a provider key and should never expose that key through `NEXT_PUBLIC_*` variables.
