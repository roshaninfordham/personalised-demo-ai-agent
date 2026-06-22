# Environment Variables

Local development uses `.env.example` copied to `.env`.

```bash
cp .env.example .env
```

Production must use Kubernetes Secrets or a secret manager. Do not commit real `.env` files.

## Default Local Mode

The free deterministic path uses fake providers:

```env
AI_TEXT_PROVIDER=fake
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
AI_EMBEDDING_PROVIDER=fake
CRM_EXPORT_PROVIDER=mock
CRM_EXPORT_DRY_RUN=true
```

## Provider Keys

Provider keys must be backend-only variables. Never prefix provider secrets with `NEXT_PUBLIC_`.

Backend-only examples:

```env
AI_TEXT_API_KEY=<your-key>
DEEPGRAM_API_KEY=<your-key>
CARTESIA_API_KEY=<your-key>
CRM_WEBHOOK_SECRET=<your-secret>
```

Frontend-safe examples:

```env
NEXT_PUBLIC_APP_NAME=Live Demo Agent
NEXT_PUBLIC_API_BASE_URL=$API_URL
NEXT_PUBLIC_ENABLE_DEBUG_PANEL=true
```

## Restart Requirements

After changing provider, database, Redis, object storage, auth, or browser sandbox variables, restart affected services:

```bash
make up api agent-runtime browser-runtime learner-worker
```

After changing `NEXT_PUBLIC_*` variables, rebuild the frontend:

```bash
make up web
```

## Production Safety

Production startup gates reject unsafe combinations such as fake providers, wildcard CORS, local product URLs, destructive browser actions, and unsandboxed Chromium.

See [production-hardening.md](../architecture/production-hardening.md).
