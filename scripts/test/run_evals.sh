#!/usr/bin/env bash
set -euo pipefail

uv run python scripts/test/validate_eval_dataset.py tests/evals/datasets
uv run python tests/evals/runners/run_agent_quality_evals.py \
  --dataset tests/evals/datasets \
  --output tests/evals/reports/eval_report.json \
  --junit-output tests/evals/reports/eval_report.xml
