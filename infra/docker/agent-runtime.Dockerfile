FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PYTHONPATH=/app/services/agent_runtime/src:/app/packages/contracts/generated/python:/app/packages/backend_common/src:/app/packages/policies/generated/python

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/agent_runtime/pyproject.toml services/agent_runtime/pyproject.toml
COPY services/learner_worker/pyproject.toml services/learner_worker/pyproject.toml
COPY services/tts_service/pyproject.toml services/tts_service/pyproject.toml
COPY services/agent_runtime services/agent_runtime
COPY packages/backend_common packages/backend_common
COPY packages/policies packages/policies
COPY packages/contracts/generated/python packages/contracts/generated/python

RUN uv sync --frozen --package live-demo-agent-runtime --no-dev
RUN chown -R app:app /app

USER app

EXPOSE 8300

CMD ["/app/.venv/bin/live-demo-agent-runtime"]
