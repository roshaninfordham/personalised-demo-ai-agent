from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    output_dir = Path(".local/test-results")
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "commit": _git_commit(),
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": "local",
        "provider_mode": "fake",
        "reports": {
            "unit": str(output_dir / "unit-results.xml"),
            "integration": str(output_dir / "integration-results.xml"),
            "e2e": str(output_dir / "e2e-results.xml"),
            "eval": "tests/evals/reports/eval_report.json",
            "k6": ".local/load-results/k6-summary.json",
            "locust": ".local/load-results/locust-stats.csv",
            "resource_leaks": ".local/load-results/resource-leak-report.json",
        },
    }
    (output_dir / "artifact-index.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


def _git_commit() -> str | None:
    head = Path(".git/HEAD")
    if not head.exists():
        return None
    value = head.read_text(errors="ignore").strip()
    if value.startswith("ref: "):
        ref = Path(".git") / value.removeprefix("ref: ").strip()
        return ref.read_text(errors="ignore").strip() if ref.exists() else None
    return value or None


if __name__ == "__main__":
    raise SystemExit(main())
