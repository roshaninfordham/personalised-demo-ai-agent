FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/agent_runtime/pyproject.toml services/agent_runtime/pyproject.toml
COPY services/learner_worker/pyproject.toml services/learner_worker/pyproject.toml
COPY services/tts_service/pyproject.toml services/tts_service/pyproject.toml
COPY services/learner_worker services/learner_worker
COPY packages/contracts/generated/python packages/contracts/generated/python

RUN uv sync --frozen --package live-demo-learner-worker --no-dev
RUN chown -R app:app /app

USER app

CMD ["/app/.venv/bin/live-demo-learner-worker"]

