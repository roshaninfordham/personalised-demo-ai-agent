# Phase 1 Acceptance Checklist

## Repository Structure

[ ] All required folders exist.
[ ] All required placeholder service entrypoints exist.
[ ] All package names are generic and consistent.
[ ] README explains the structure.
[ ] No company-specific or target-product-specific package names exist.

## Python Tooling

[ ] uv workspace is configured.
[ ] Python services use src layout.
[ ] Ruff is configured.
[ ] mypy strict mode is configured.
[ ] pytest is configured.
[ ] Python smoke tests pass.
[ ] No duplicate Python DTOs exist outside contracts.

## TypeScript Tooling

[ ] pnpm workspace is configured.
[ ] TypeScript strict mode is configured.
[ ] ESLint flat config is configured.
[ ] Prettier is configured.
[ ] Vitest is configured.
[ ] TypeScript smoke tests pass.
[ ] No duplicate TypeScript DTOs exist outside contracts.

## Contracts

[ ] JSON schemas exist for all required domains.
[ ] Schemas validate.
[ ] Generated Python contracts exist or generator TODO is explicit.
[ ] Generated TypeScript contracts exist or generator TODO is explicit.
[ ] Contracts use snake_case wire format.
[ ] additionalProperties is false by default.
[ ] Event envelope includes trace_id and created_at.
[ ] Browser action result includes latency_ms.
[ ] Lead insights require evidence references.

## Docker Compose

[ ] docker-compose.yml exists.
[ ] docker compose config succeeds.
[ ] Default stack excludes heavy AI/observability services.
[ ] Optional profiles exist for ai-local, tts-local, and observability.
[ ] Postgres uses pgvector image.
[ ] Redis has persistent append-only config.
[ ] MinIO has fixed API and console ports.
[ ] Services have health checks where practical.
[ ] No service runs privileged.
[ ] No secrets are baked into images.

## Security

[ ] .env is ignored.
[ ] .env.example is committed.
[ ] No real secrets exist in the repo.
[ ] Frontend receives no provider API secrets.
[ ] Docker images do not copy .env.
[ ] Containers use non-root users where practical.
[ ] README includes local-secret warning.

## Determinism

[ ] uv.lock is committed.
[ ] pnpm-lock.yaml is committed.
[ ] Contract generation is deterministic.
[ ] Formatting is deterministic.
[ ] Generated files are either reproducible or explicitly deferred.

## Resource Efficiency

[ ] Default stack does not download model weights.
[ ] Default stack does not require GPU.
[ ] Heavy services are opt-in through profiles.
[ ] No unnecessary AI/browser packages are installed in skeleton services.
