FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.5.31 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/agent_runtime/pyproject.toml services/agent_runtime/pyproject.toml
COPY services/learner_worker/pyproject.toml services/learner_worker/pyproject.toml
COPY services/tts_service/pyproject.toml services/tts_service/pyproject.toml
COPY packages/backend_common packages/backend_common
COPY packages/policies packages/policies
COPY packages/contracts/generated/python packages/contracts/generated/python
COPY services/agent_runtime services/agent_runtime

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --package live-demo-agent-runtime --no-dev

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONPATH=/app/services/agent_runtime/src:/app/packages/contracts/generated/python:/app/packages/backend_common/src:/app/packages/policies/generated/python

WORKDIR /app

RUN groupadd --system --gid 10001 app \
  && useradd --system --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin app \
  && mkdir -p /app /tmp /app/.cache \
  && chown -R 10001:10001 /app /tmp

COPY --from=builder --chown=10001:10001 /app /app

USER 10001:10001

EXPOSE 8300

CMD ["/app/.venv/bin/live-demo-agent-runtime"]
