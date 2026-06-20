# Live Demo Agent

Monorepo foundation for a production-grade, low-latency, secure, deterministic, provider-agnostic AI product-demo agent platform.

Phase 2 provides the monorepo, contracts, tooling, durable database schema, Redis live-state layer, Redis Streams event bus, and S3-compatible artifact storage foundation. It does not yet implement the live AI demo loop.

## What This Repo Is

The eventual system will run a live AI product-demo agent that opens a product URL in an isolated browser, learns the interface, speaks with a user in real time, controls the browser through safe actions, answers from grounded UI evidence, and creates CRM-ready sales intelligence.

This repository currently contains:

- Phase 0 architecture and product requirements.
- Phase 1 monorepo scaffold.
- Phase 2 database, Redis, event bus, and artifact storage foundation.
- Python and TypeScript workspace tooling.
- Shared JSON Schema contracts with generated Python and TypeScript outputs.
- Local Docker Compose stack for lightweight development.
- Observability placeholders.

## System Components

```mermaid
flowchart TB
    User["User / Prospect"]

    subgraph Web["apps/web"]
        Start["Demo start skeleton"]
        Panels["Call / browser / transcript panels"]
    end

    subgraph PythonServices["Python services"]
        API["services/api"]
        Agent["services/agent_runtime"]
        Learner["services/learner_worker"]
        TTS["services/tts_service"]
    end

    subgraph TypeScriptServices["TypeScript services"]
        Browser["services/browser_runtime"]
    end

    subgraph Contracts["packages/contracts"]
        Schemas["JSON Schemas"]
        PyModels["Generated Pydantic models"]
        TsTypes["Generated TypeScript types"]
    end

    subgraph Infra["infra"]
        Compose["Docker Compose"]
        Postgres["Postgres + pgvector"]
        Redis["Redis live state + streams"]
        MinIO["MinIO/S3 artifacts"]
        Observability["Observability placeholders"]
    end

    User --> Web
    Web --> API
    API --> Contracts
    Agent --> Contracts
    Learner --> Contracts
    TTS --> Contracts
    Browser --> Contracts
    Compose --> Web
    Compose --> API
    Compose --> Agent
    Compose --> Browser
    Compose --> Learner
    Compose --> Postgres
    Compose --> Redis
    Compose --> MinIO
    Compose --> Infra
```

## Dependency Graph

The dependency graph is intentionally acyclic.

```mermaid
flowchart LR
    Contracts["packages/contracts"]
    Web["apps/web"]
    API["services/api"]
    Agent["services/agent_runtime"]
    Browser["services/browser_runtime"]
    Learner["services/learner_worker"]
    TTS["services/tts_service"]
    Infra["infra/*"]
    Tests["tests/*"]

    Web --> Contracts
    API --> Contracts
    Agent --> Contracts
    Browser --> Contracts
    Learner --> Contracts
    TTS --> Contracts
    Infra --> Web
    Infra --> API
    Infra --> Agent
    Infra --> Browser
    Infra --> Learner
    Infra --> TTS
    Tests --> Contracts
    Tests --> API
    Tests --> Agent
    Tests --> Browser
    Tests --> Learner
    Tests --> TTS
```

Forbidden directions:

- `packages/contracts` must not import apps or services.
- `services/api` must not import `apps/web`.
- `services/browser_runtime` must not import Python service internals.
- `apps/web` must not import backend secrets or provider adapters.

## Folder Structure

```text
.
|-- apps
|   `-- web
|-- architecture
|-- infra
|   |-- docker
|   `-- observability
|-- packages
|   `-- contracts
|       |-- schemas
|       |-- generated
|       `-- scripts
|-- services
|   |-- api
|   |-- agent_runtime
|   |-- browser_runtime
|   |-- learner_worker
|   `-- tts_service
|-- tests
|   |-- integration
|   `-- e2e
|-- docker-compose.yml
|-- Makefile
|-- package.json
|-- pnpm-workspace.yaml
|-- pyproject.toml
`-- .env.example
```

## Local Prerequisites

- Python `>=3.12,<3.14`.
- `uv` with workspace support. This repo was verified with `uv 0.11.7`.
- Node `>=20`. This repo was verified with Node `24.13.1`.
- pnpm `>=9`. This repo was verified with pnpm `10.30.1`.
- Docker and Docker Compose for the local stack.

## Local Setup

```bash
cp .env.example .env
pnpm install
uv sync --all-packages
make contracts
make lint
make test
docker compose up --build
```

`uv sync --all-packages` is supported by the local `uv 0.11.7` toolchain and syncs every Python workspace package.

## Common Commands

```bash
make install
make contracts
make lint
make format
make format-write
make typecheck
make test
make docker-config
make docker-up
make docker-down
make db-upgrade
make db-current
make db-downgrade
make secrets-check
```

Python-only:

```bash
uv sync --all-packages
uv run ruff check .
uv run ruff format --check .
uv run mypy services packages/contracts/generated/python tests
uv run pytest
```

TypeScript-only:

```bash
pnpm install
pnpm lint
pnpm format
pnpm typecheck
pnpm test
```

## Docker Compose

Default lightweight stack:

```bash
docker compose up --build
```

Include local LLM runtime:

```bash
docker compose --profile ai-local up --build
```

Include local TTS service:

```bash
docker compose --profile tts-local up --build
```

Include observability stack:

```bash
docker compose --profile observability up --build
```

Include everything:

```bash
docker compose --profile ai-local --profile tts-local --profile observability up --build
```

```mermaid
flowchart TB
    Default["Default stack"]
    Web["web"]
    API["api"]
    Agent["agent-runtime"]
    Browser["browser-runtime"]
    Learner["learner-worker"]
    Postgres["postgres / pgvector"]
    Redis["redis"]
    Minio["minio"]
    AI["profile: ai-local / ollama"]
    TTS["profile: tts-local / tts-service"]
    Obs["profile: observability"]

    Default --> Web
    Default --> API
    Default --> Agent
    Default --> Browser
    Default --> Learner
    Default --> Postgres
    Default --> Redis
    Default --> Minio
    Default -.optional.-> AI
    Default -.optional.-> TTS
    Default -.optional.-> Obs
```

The default stack does not start Ollama, Grafana, Prometheus, Loki, Jaeger, or local TTS.

## Phase 2 Storage Architecture

Phase 2 uses a strict storage split:

```mermaid
flowchart TB
    API["services/api"]
    Postgres["Postgres 16 + pgvector\nDurable system of record"]
    Redis["Redis 7\nEphemeral live state + streams"]
    MinIO["MinIO/S3\nLarge binary artifacts"]

    API --> Postgres
    API --> Redis
    API --> MinIO

    Postgres --> Durable["organizations, users, products, recipes, sessions,\nscreens, transcripts, actions, lead summaries,\nmodel invocations, audit logs, artifact metadata, outbox"]
    Redis --> Hot["current screen, safe actions, transcript window,\nlatency state, browser status, locks, stream fanout"]
    MinIO --> Blobs["screenshots, recordings, browser traces,\ngenerated reports, model debug artifacts"]
```

Rules:

- Durable business records belong in Postgres.
- Hot-path live context belongs in compact Redis keys.
- Screenshots, recordings, traces, and reports belong in MinIO/S3, with only metadata in Postgres.
- Artifact rows store `bucket` and `object_key`, never public URLs.
- Redis streams are capped with `MAXLEN ~ REDIS_EVENT_STREAM_MAXLEN`.
- Audit logs are append-only and do not have `updated_at` or `deleted_at`.

## Database and Migrations

Start storage dependencies:

```bash
docker compose up -d postgres redis minio
```

Apply migrations:

```bash
make db-upgrade
make db-current
make db-history
```

Rollback one migration:

```bash
make db-downgrade
```

Create a future migration:

```bash
make db-revision m="describe change"
```

The Alembic environment reads `DATABASE_SYNC_URL` for host-side migrations. `.env.example` uses `localhost` so `make db-upgrade` works from the host. Docker Compose overrides database, Redis, and object-storage endpoints inside containers to use service DNS names.

```mermaid
flowchart LR
    Models["SQLAlchemy metadata"]
    Alembic["Alembic migration scripts"]
    Postgres["Postgres + pgvector"]
    Outbox["event_outbox"]
    RedisStreams["Redis Streams"]

    Models --> Alembic
    Alembic --> Postgres
    Postgres --> Outbox
    Outbox -.future publisher.-> RedisStreams
```

Inspect Postgres:

```bash
docker compose exec postgres psql -U demo_agent -d demo_agent
\dt
\di
select * from alembic_version;
```

## Redis Live State and Events

Redis keys are centralized under `services/api/src/live_demo_api/live_state/redis_keys.py`.

```mermaid
flowchart TB
    Session["live_demo:session:{session_id}:state"]
    Screen["live_demo:session:{session_id}:current_screen"]
    Actions["live_demo:session:{session_id}:safe_actions"]
    Transcript["live_demo:session:{session_id}:transcript_window"]
    Latency["live_demo:session:{session_id}:latency"]
    Stream["live_demo:stream:session:{session_id}:events"]
    Global["live_demo:stream:global:events"]

    ContextBuilder["Future realtime context builder"] --> Session
    ContextBuilder --> Screen
    ContextBuilder --> Actions
    ContextBuilder --> Transcript
    ContextBuilder --> Latency
    EventBus["RedisStreamEventBus"] --> Stream
    EventBus --> Global
```

Inspect Redis:

```bash
docker compose exec redis redis-cli
keys live_demo:*
xrange live_demo:stream:global:events - +
xinfo stream live_demo:stream:global:events
```

## Object Storage

Object keys are deterministic and tenant scoped:

```text
org/{organization_id}/sessions/{session_id}/screenshots/{screen_id}.webp
org/{organization_id}/sessions/{session_id}/browser-traces/{trace_id}.zip
org/{organization_id}/sessions/{session_id}/recordings/{recording_id}.wav
org/{organization_id}/sessions/{session_id}/reports/{report_name}.json
```

```mermaid
sequenceDiagram
    participant Runtime as Future browser/agent runtime
    participant API as API storage layer
    participant S3 as MinIO/S3 bucket
    participant DB as artifact_objects table

    Runtime->>API: artifact bytes + metadata
    API->>S3: put object by deterministic key
    S3-->>API: etag
    API->>DB: insert bucket/object_key metadata
    API-->>Runtime: artifact_id
```

Inspect MinIO:

- API: `http://localhost:9000`
- Console: `http://localhost:9001`
- Local credentials are from `.env.example` and are not production credentials.

## Phase 2 Test Commands

```bash
docker compose up -d postgres redis minio
make db-upgrade
make db-current
uv run pytest services/api/tests/test_db_models.py
uv run pytest services/api/tests/test_alembic_migrations.py
uv run pytest services/api/tests/test_redis_keys.py
uv run pytest services/api/tests/test_live_state_store.py
uv run pytest services/api/tests/test_event_bus.py
uv run pytest services/api/tests/test_artifact_store.py
```

## How Contracts Work

JSON Schema is the source of truth:

```mermaid
flowchart LR
    Schemas["packages/contracts/schemas/*.schema.json"]
    Validate["validate-schemas.ts"]
    PyGen["generate-python-contracts.py"]
    TsGen["generate-typescript-contracts.ts"]
    PyOut["generated/python/live_demo_contracts"]
    TsOut["generated/typescript/src"]
    Services["apps and services"]

    Schemas --> Validate
    Schemas --> PyGen
    Schemas --> TsGen
    PyGen --> PyOut
    TsGen --> TsOut
    PyOut --> Services
    TsOut --> Services
```

Run:

```bash
make contracts
git diff --exit-code packages/contracts/generated
```

Generated files are marked with "Do not edit manually."

## Provider Configuration Summary

Provider choices are configured with generic environment variables:

- `AI_TEXT_*`
- `AI_VISION_*`
- `AI_EMBEDDING_*`
- `AI_STT_*`
- `AI_TTS_*`
- `BROWSER_*`
- `TRANSPORT_*`

Vendor-specific secrets are backend-only. Do not expose provider keys to the frontend and do not add `NEXT_PUBLIC_` provider key variables.

## Security Notes

- `.env` and `.env.*` are ignored.
- `.env.example` contains local-only placeholder credentials; do not use them in production.
- Docker images do not copy `.env`.
- Frontend code must not receive provider API keys.
- Database, Redis values, event payloads, object metadata, and audit logs must not contain secrets.
- Browser screenshots are treated as sensitive artifacts.
- Object buckets are not public; future access must use backend-generated signed URLs.
- Raw prompts are not stored in `model_invocations` by default.
- Raw audio is not stored in `transcript_events`.
- Browser runtime does not run privileged and does not use host networking.
- Heavy local AI services are opt-in profiles.
- `make secrets-check` is a placeholder for adding gitleaks or equivalent in CI.

## Troubleshooting

If `uv sync --all-packages` fails because no compatible Python is installed, allow `uv` to install Python `3.12` or install Python `3.12` manually.

The contracts package uses `python3` for generation because this environment does not provide a `python` shim.

If `pnpm install` uses a different pnpm version, ensure it is at least pnpm `9`. The committed lockfile is generated with pnpm `10.30.1`.

If `docker compose config` fails because `.env` is missing, run:

```bash
cp .env.example .env
```

If Docker build fails on frozen lockfiles, rerun dependency installation and commit the updated lockfiles:

```bash
pnpm install
uv sync --all-packages
```

## Phase 2 Limitations

- Realtime voice and Pipecat pipeline are not implemented in Phase 2.
- Browser automation and Playwright control are not implemented in Phase 2.
- Product learning, summarization, and graph building are not implemented in Phase 2.
- CRM export is not implemented in Phase 2.
- Event outbox publisher worker is not implemented yet; Phase 2 creates the outbox table and Redis event bus foundation.
- Observability configs are placeholders until runtime metrics and traces are emitted.

## Architecture Docs

- [Phase 0 product requirements](architecture/phase_0_product_requirements.md)
- [Phase 0 system architecture](architecture/phase_0_system_architecture.md)
- [Phase 0 provider abstractions](architecture/phase_0_provider_abstractions.md)
- [Phase 0 environment contract](architecture/phase_0_environment_contract.md)
- [Phase 1 acceptance checklist](architecture/phase_1_acceptance_checklist.md)
- [Phase 2 acceptance checklist](architecture/phase_2_acceptance_checklist.md)
