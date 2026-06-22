API_PYTHONPATH := services/api/src:packages/contracts/generated/python:packages/policies/generated/python:packages/backend_common/src
LEARNER_PYTHONPATH := services/learner_worker/src:packages/backend_common/src:packages/policies/generated/python:packages/contracts/generated/python

.PHONY: help up up-lite up-full up-observability up-ai-local up-nim up-scrapegraph down restart logs status health open doctor debug-session clean clean-docker clean-docker-safe clean-docker-deep rebuild rebuild-service test-e2e-user test-e2e-real-demo test-login-required-flow test-voice-text-flow test-rebolt-demo test-e2e-full test-ui-ux test-ready verify-ui verify-realtime verify-e2e-demo verify-agentic-demo deploy-check final-ready-lite final-ready readiness-report design-lint design-export design-check production-config-test install lint format format-write typecheck test contracts docker-config docker-up docker-down db-upgrade db-downgrade db-revision db-current db-history db-reset api-dev api-test api-test-integration api-openapi ai-test ai-test-live ai-test-unit browser-install browser-dev browser-test browser-test-integration web-dev web-build web-test web-typecheck web-lint agent-dev agent-test agent-test-integration agent-build agent-brain-test agent-brain-test-integration policy-validate policy-generate policy-test policy-test-ts policy-test-py policy-fixtures-check learner-dev learner-worker learner-test learner-test-integration recipe-test recipe-test-integration recipe-validate-fixtures orchestration-test orchestration-test-integration orchestration-smoke post-demo-test post-demo-test-integration post-demo-smoke obs-up obs-down obs-test obs-dashboards-validate obs-smoke test-unit test-integration test-browser test-session-lifecycle test-e2e test-evals test-load-smoke test-load-local test-all-quality test-fixture-secrets docker-build-all docker-scan k8s-render k8s-validate security-scan ci-local deploy-staging deploy-production rollback-staging rollback-production docs-validate docs-links docs-secrets docs-mermaid docs-index docs-all py-sync py-lint py-format py-typecheck py-test ts-install ts-lint ts-format ts-typecheck ts-test secrets-check

help:
	@echo "Available commands:"
	@echo "  make install          Install Python and TypeScript dependencies"
	@echo "  make up               Start default local demo stack"
	@echo "  make up-lite          Start low-memory fake-provider stack"
	@echo "  make doctor           Show local diagnostics and Docker disk usage"
	@echo "  make final-ready      Run final readiness gate"
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
	@echo "  make browser-test     Run browser runtime unit tests"
	@echo "  make web-test         Run frontend unit tests"
	@echo "  make web-dev          Run frontend development server"
	@echo "  make agent-brain-test Run realtime agent brain tests"
	@echo "  make recipe-test      Run demo recipe engine tests"
	@echo "  make test-all-quality Run Phase 15 safety, integration, e2e, eval, and load smoke gates"
	@echo "  make ci-local         Run Phase 16 local CI gate"
	@echo "  make docker-build-all Build hardened service images"
	@echo "  make k8s-validate     Render and validate Kubernetes manifests"
	@echo "  make docs-all         Generate and validate documentation"
	@echo "  make docker-config    Validate Docker Compose config"
	@echo "  make docker-up        Start local stack"
	@echo "  make docker-down      Stop local stack"
	@echo "  make clean            Remove caches"

up:
	scripts/dev/up.sh default

up-lite:
	scripts/dev/up.sh lite

up-full:
	scripts/dev/up.sh full

up-observability:
	scripts/dev/up.sh observability

up-ai-local:
	scripts/dev/up.sh ai-local

up-nim:
	scripts/dev/up.sh nim

up-scrapegraph:
	scripts/dev/up.sh scrapegraph

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=200

status:
	docker compose ps

health:
	scripts/dev/health_check.sh

open:
	scripts/dev/open_local.sh

doctor:
	scripts/dev/doctor.sh

debug-session:
	scripts/dev/debug_session.sh $(session)

clean-docker:
	make clean-docker-safe

clean-docker-safe:
	scripts/dev/docker_clean_safe.sh

clean-docker-deep:
	scripts/dev/docker_clean_deep.sh

rebuild:
	docker compose build

rebuild-service:
	docker compose build $(service)

test-e2e-user:
	pnpm exec playwright test -c tests/e2e/playwright.config.ts tests/e2e/user-demo.spec.ts --headed

test-e2e-real-demo:
	pnpm exec playwright test -c tests/e2e/playwright.config.ts tests/e2e/real-url-demo.spec.ts --headed

test-login-required-flow:
	pnpm exec playwright test -c tests/e2e/playwright.config.ts tests/e2e/login-required-flow.spec.ts --headed

test-voice-text-flow:
	pnpm exec playwright test -c tests/e2e/playwright.config.ts tests/e2e/voice-or-text-agent-demo.spec.ts --headed

test-rebolt-demo:
	pnpm exec playwright test -c tests/e2e/playwright.config.ts tests/e2e/rebolt-metric-master-demo.spec.ts --headed

test-e2e-full:
	make test-fixture-secrets
	make test-unit
	make test-browser
	make test-session-lifecycle
	make test-e2e
	make test-evals

test-ui-ux:
	pnpm exec playwright test -c tests/e2e/playwright.config.ts tests/e2e/ui-ux.spec.ts --headed

test-ready:
	make health
	make test-e2e-user
	make obs-smoke

verify-ui:
	make web-typecheck
	make web-lint
	make web-test

verify-realtime:
	make health
	make test-e2e-real-demo

verify-e2e-demo:
	make test-e2e-real-demo

verify-agentic-demo:
	make health
	make test-login-required-flow
	make test-voice-text-flow

deploy-check:
	make ci-local
	make k8s-validate
	make docker-scan

design-lint:
	npx @google/design.md lint DESIGN.md
	npx @google/design.md lint apps/web/DESIGN.md

design-export:
	uv run python scripts/design/export_design_tokens.py

design-check:
	make design-lint
	make design-export
	git diff --exit-code -- apps/web/app/design-tokens.css

production-config-test:
	uv run pytest services/api/tests/test_production_safety_gates.py
	pnpm --filter @live-demo-agent/browser-runtime test -- config

readiness-report:
	uv run python scripts/dev/generate_readiness_report.py

final-ready-lite:
	COMPOSE_DETACHED=true scripts/dev/up.sh lite
	HEALTH_ATTEMPTS=15 HEALTH_RETRY_SECONDS=2 make health
	make test-e2e-real-demo
	make verify-agentic-demo
	make test-fixture-secrets
	make docs-secrets
	scripts/dev/docker_disk_usage.sh
	READINESS_E2E_PASSED=true \
	READINESS_CURSOR_EVENTS_SEEN=true \
	READINESS_SAFE_CLICK_EXECUTED=true \
	READINESS_POLICY_BLOCK_VERIFIED=true \
	READINESS_LEAD_SUMMARY_READY=true \
	READINESS_HALLUCINATION_COUNT=0 \
	READINESS_SAFETY_VIOLATIONS=0 \
	make readiness-report

final-ready:
	make docs-secrets
	make test-fixture-secrets
	make contracts
	make policy-validate
	make lint
	make typecheck
	make test-unit
	make test-browser
	make test-session-lifecycle
	make test-e2e-user
	make test-evals
	make docker-build-all
	scripts/security/verify_no_env_in_images.sh
	scripts/security/verify_container_user.sh
	scripts/dev/docker_disk_usage.sh
	make obs-dashboards-validate
	make production-config-test
	make readiness-report

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
	make up

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

browser-install:
	pnpm --filter @live-demo-agent/browser-runtime install

browser-dev:
	pnpm --filter @live-demo-agent/browser-runtime dev

browser-test:
	pnpm --filter @live-demo-agent/browser-runtime test

browser-test-integration:
	pnpm --filter @live-demo-agent/browser-runtime test:integration

web-dev:
	pnpm --filter @live-demo-agent/web dev

web-build:
	pnpm --filter @live-demo-agent/web build

web-test:
	pnpm --filter @live-demo-agent/web test

web-typecheck:
	pnpm --filter @live-demo-agent/web typecheck

web-lint:
	pnpm --filter @live-demo-agent/web lint

agent-dev:
	uv run --package live-demo-agent-runtime uvicorn live_demo_agent_runtime.main:app --reload --host 0.0.0.0 --port 8300

agent-test:
	uv run pytest services/agent_runtime/tests -m "not integration"

agent-test-integration:
	uv run pytest services/agent_runtime/tests -m integration

agent-build:
	docker compose build agent-runtime

agent-brain-test:
	uv run pytest services/agent_runtime/tests \
		-k "context or output_validator or tool_router or demo_planner or persona or memory or realtime_agent"

agent-brain-test-integration:
	uv run pytest services/agent_runtime/tests -m agent_brain_integration

learner-dev:
	PYTHONPATH=$(LEARNER_PYTHONPATH) uv run --package live-demo-learner-worker python -m live_demo_learner_worker.main

learner-worker:
	PYTHONPATH=$(LEARNER_PYTHONPATH) uv run --package live-demo-learner-worker python -m live_demo_learner_worker.main

learner-test:
	uv run pytest services/learner_worker/tests -m "not integration"

learner-test-integration:
	uv run pytest services/learner_worker/tests -m integration

recipe-test:
	uv run pytest tests/recipes -m "not integration"

recipe-test-integration:
	uv run pytest tests/recipes -m integration

recipe-validate-fixtures:
	uv run pytest tests/recipes/test_recipe_schema_validator.py

orchestration-test:
	uv run pytest services/api/tests \
		-k "orchestration or prewarm or recovery or shutdown or browser_agent_sync" \
		-m "not integration"

orchestration-test-integration:
	uv run pytest services/api/tests -m orchestration_integration

orchestration-smoke:
	make health

post-demo-test:
	uv run pytest services/api/tests \
		-k "post_demo or lead_insight or feature_shown or lead_summary or crm" \
		-m "not integration"

post-demo-test-integration:
	uv run pytest services/api/tests -m post_demo_integration

post-demo-smoke:
	make health

obs-up:
	scripts/dev/up.sh observability

obs-down:
	docker compose --profile observability down

obs-test:
	uv run pytest tests/observability services/api/tests services/agent_runtime/tests services/learner_worker/tests -k "observability or metrics or tracing or logging or latency"

obs-dashboards-validate:
	uv run python scripts/validate_grafana_dashboards.py infra/observability/grafana/dashboards

obs-smoke:
	scripts/dev/obs_smoke.sh

test-fixture-secrets:
	uv run python scripts/test/check_no_secrets_in_fixtures.py

test-unit:
	mkdir -p .local/test-results
	uv run pytest tests/unit services/api/tests services/agent_runtime/tests services/learner_worker/tests \
		-m "not integration" \
		--junitxml=.local/test-results/unit-results.xml
	pnpm test

test-integration:
	mkdir -p .local/test-results
	uv run pytest tests/integration services/api/tests services/agent_runtime/tests services/learner_worker/tests \
		-m integration \
		--junitxml=.local/test-results/integration-results.xml

test-browser:
	pnpm --filter @live-demo-agent/browser-runtime test:integration

test-session-lifecycle:
	mkdir -p .local/test-results
	uv run pytest tests/integration/session_lifecycle -m integration \
		--junitxml=.local/test-results/integration-results.xml

test-e2e:
	pnpm exec playwright test -c tests/e2e/playwright.config.ts

test-evals:
	uv run python scripts/test/validate_eval_dataset.py tests/evals/datasets
	uv run python tests/evals/runners/run_agent_quality_evals.py \
		--dataset tests/evals/datasets \
		--output tests/evals/reports/eval_report.json \
		--junit-output tests/evals/reports/eval_report.xml

test-load-smoke:
	mkdir -p .local/load-results
	if command -v k6 >/dev/null 2>&1; then \
		k6 run --summary-export=.local/load-results/k6-summary.json tests/load/k6/api-smoke.js; \
	else \
		uv run python scripts/test/run_k6_smoke_fallback.py; \
	fi

test-load-local:
	mkdir -p .local/load-results
	if command -v locust >/dev/null 2>&1; then \
		locust -f tests/load/locustfile.py --headless -u 5 -r 1 -t 5m \
			--csv .local/load-results/locust \
			--html .local/load-results/locust.html; \
	else \
		uv run python scripts/test/run_locust_fallback.py; \
	fi

test-all-quality:
	make test-fixture-secrets
	make test-unit
	make test-browser
	make test-session-lifecycle
	make test-e2e
	make test-evals
	make test-load-smoke
	uv run python scripts/test/collect_test_artifacts.py

docker-build-all:
	docker build -f infra/docker/web.Dockerfile -t live-demo-agent/web:local .
	docker build -f infra/docker/api.Dockerfile -t live-demo-agent/api:local .
	docker build -f infra/docker/agent-runtime.Dockerfile -t live-demo-agent/agent-runtime:local .
	docker build -f infra/docker/browser-runtime.Dockerfile -t live-demo-agent/browser-runtime:local .
	docker build -f infra/docker/learner-worker.Dockerfile -t live-demo-agent/learner-worker:local .
	docker build -f infra/docker/post-demo-worker.Dockerfile -t live-demo-agent/post-demo-worker:local .

docker-scan:
	scripts/security/scan_images.sh

k8s-render:
	scripts/k8s/render_manifests.sh staging
	scripts/k8s/render_manifests.sh production

k8s-validate:
	scripts/k8s/validate_manifests.sh

security-scan:
	scripts/security/scan_secrets.sh
	scripts/security/scan_dependencies.sh
	scripts/security/scan_k8s_manifests.sh

ci-local:
	make contracts
	make policy-validate
	make lint
	make typecheck
	make test-unit
	make docker-build-all
	make security-scan
	make k8s-validate

deploy-staging:
	scripts/deploy/deploy_staging.sh

deploy-production:
	scripts/deploy/deploy_production.sh

rollback-staging:
	scripts/deploy/rollback.sh staging

rollback-production:
	scripts/deploy/rollback.sh production

docs-index:
	uv run python scripts/docs/generate_docs_index.py

docs-secrets:
	uv run python scripts/docs/check_no_secrets_in_docs.py

docs-validate:
	scripts/docs/validate_docs.sh

docs-links:
	scripts/docs/check_links.sh

docs-mermaid:
	scripts/docs/check_mermaid.sh

docs-all:
	make docs-index
	make docs-secrets
	make docs-validate
	make docs-links
	make docs-mermaid

policy-validate:
	pnpm --filter @live-demo-agent/policies validate

policy-generate:
	pnpm --filter @live-demo-agent/policies generate

policy-test-py:
	uv run pytest packages/backend_common/src/live_demo_backend_common/tests/policy services/api/tests/test_rbac.py services/api/tests/test_audit_logging.py

policy-test-ts:
	pnpm --filter @live-demo-agent/browser-runtime test -- policy

policy-test:
	make policy-validate
	make policy-generate
	make policy-test-py
	make policy-test-ts

policy-fixtures-check:
	uv run pytest tests/security/test_cross_service_policy_consistency.py

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache node_modules/.cache apps/web/.next .local/test-artifacts
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
