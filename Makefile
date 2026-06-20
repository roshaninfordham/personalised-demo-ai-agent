API_PYTHONPATH := services/api/src:packages/contracts/generated/python

.PHONY: help install lint format format-write typecheck test contracts docker-config docker-up docker-down clean db-upgrade db-downgrade db-revision db-current db-history db-reset api-dev api-test api-test-integration api-openapi ai-test ai-test-live ai-test-unit py-sync py-lint py-format py-typecheck py-test ts-install ts-lint ts-format ts-typecheck ts-test secrets-check

help:
	@echo "Available commands:"
	@echo "  make install          Install Python and TypeScript dependencies"
	@echo "  make lint             Run Python and TypeScript linters"
	@echo "  make format           Check formatting"
	@echo "  make format-write     Apply formatting"
	@echo "  make typecheck        Run mypy and TypeScript type checks"
	@echo "  make test             Run all tests"
	@echo "  make contracts        Validate and generate contracts"
	@echo "  make db-upgrade       Apply API database migrations"
	@echo "  make db-current       Show current API database migration"
	@echo "  make api-dev          Run API development server"
	@echo "  make api-test         Run API tests excluding integration markers"
	@echo "  make api-openapi      Export OpenAPI JSON"
	@echo "  make ai-test          Run AI provider abstraction tests without live providers"
	@echo "  make docker-config    Validate Docker Compose config"
	@echo "  make docker-up        Start local stack"
	@echo "  make docker-down      Stop local stack"
	@echo "  make clean            Remove caches"

install:
	uv sync --all-packages
	pnpm install

lint:
	uv run ruff check .
	pnpm lint

format:
	uv run ruff format --check .
	pnpm format

format-write:
	uv run ruff format .
	pnpm format:write

typecheck:
	uv run mypy services packages/backend_common/src packages/contracts/generated/python tests
	pnpm typecheck

test:
	uv run pytest
	pnpm test

contracts:
	pnpm --filter @live-demo-agent/contracts validate
	pnpm --filter @live-demo-agent/contracts generate

docker-config:
	docker compose config

docker-up:
	docker compose up --build

docker-down:
	docker compose down

db-upgrade:
	cd services/api && uv run alembic upgrade head

db-downgrade:
	cd services/api && uv run alembic downgrade -1

db-current:
	cd services/api && uv run alembic current

db-history:
	cd services/api && uv run alembic history

db-revision:
	cd services/api && uv run alembic revision --autogenerate -m "$(m)"

db-reset:
	docker compose down -v
	docker compose up -d postgres
	cd services/api && uv run alembic upgrade head

api-dev:
	PYTHONPATH=$(API_PYTHONPATH) uv run --package live-demo-api uvicorn live_demo_api.main:app --reload --host 0.0.0.0 --port 8000

api-test:
	uv run pytest services/api/tests -m "not integration"

api-test-integration:
	uv run pytest services/api/tests -m integration

api-openapi:
	@PYTHONPATH=$(API_PYTHONPATH) uv run python -m live_demo_api.export_openapi

ai-test:
	uv run pytest packages/backend_common/src/live_demo_backend_common/tests/ai -m "not live"

ai-test-live:
	RUN_LIVE_PROVIDER_TESTS=true uv run pytest packages/backend_common/src/live_demo_backend_common/tests/ai -m live

ai-test-unit:
	uv run pytest packages/backend_common/src/live_demo_backend_common/tests/ai

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +

py-sync:
	uv sync --all-packages

py-lint:
	uv run ruff check .

py-format:
	uv run ruff format .

py-typecheck:
	uv run mypy services packages/backend_common/src packages/contracts/generated/python tests

py-test:
	uv run pytest

ts-install:
	pnpm install

ts-lint:
	pnpm lint

ts-format:
	pnpm format

ts-typecheck:
	pnpm typecheck

ts-test:
	pnpm test

secrets-check:
	@echo "TODO: Add gitleaks or equivalent in CI."
