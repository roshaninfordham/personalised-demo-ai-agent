FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PYTHONPATH=/app/services/api/src:/app/packages/contracts/generated/python:/app/packages/backend_common/src:/app/packages/policies/generated/python

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/*

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/agent_runtime/pyproject.toml services/agent_runtime/pyproject.toml
COPY services/learner_worker/pyproject.toml services/learner_worker/pyproject.toml
COPY services/tts_service/pyproject.toml services/tts_service/pyproject.toml
COPY packages/backend_common packages/backend_common
COPY packages/policies packages/policies
COPY services/api services/api
COPY packages/contracts/generated/python packages/contracts/generated/python

RUN uv sync --frozen --package live-demo-api --no-dev
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "live_demo_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
