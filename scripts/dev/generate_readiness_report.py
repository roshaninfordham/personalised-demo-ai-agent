#!/usr/bin/env python3
"""Generate a local final-readiness report."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / ".local/readiness"


def run(command: list[str]) -> str:
    try:
        output = subprocess.check_output(  # noqa: S603
            command,
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        )
        return output.strip()
    except Exception as exc:
        return f"unavailable: {exc}"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    git_sha = run(["git", "rev-parse", "HEAD"])
    docker_df = run(["docker", "system", "df"])
    compose_ps = run(["docker", "compose", "ps", "--format", "json"])
    report: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_sha": git_sha,
        "environment": os.getenv("APP_ENV", "local"),
        "provider_mode": {
            "llm": os.getenv("AI_TEXT_PROVIDER", "fake"),
            "stt": os.getenv("AI_STT_PROVIDER", "fake"),
            "tts": os.getenv("AI_TTS_PROVIDER", "fake"),
        },
        "docker": {
            "disk_usage_before": docker_df,
            "disk_usage_after": docker_df,
            "images_built": [],
            "image_sizes": {},
        },
        "services": {
            "compose": compose_ps,
        },
        "e2e": {
            "passed": None,
            "first_screen_ms": None,
            "cursor_events_seen": None,
            "safe_click_executed": None,
            "policy_block_verified": None,
            "lead_summary_ready": None,
        },
        "quality": {
            "hallucination_count": None,
            "safety_violations": None,
            "grounding_score": None,
        },
        "resource_cleanup": {
            "active_browser_sessions_after_end": None,
            "active_voice_sessions_after_end": None,
            "stale_locks": None,
        },
    }
    report_json = json.dumps(report, indent=2) + "\n"
    (OUT_DIR / "final-readiness-report.json").write_text(
        report_json,
        encoding="utf-8",
    )
    (OUT_DIR / "final-readiness-report.md").write_text(
        "\n".join(
            [
                "# Final Readiness Report",
                "",
                f"- Timestamp: `{report['timestamp']}`",
                f"- Git SHA: `{git_sha}`",
                f"- Environment: `{report['environment']}`",
                f"- LLM provider: `{report['provider_mode']['llm']}`",
                f"- STT provider: `{report['provider_mode']['stt']}`",
                f"- TTS provider: `{report['provider_mode']['tts']}`",
                "",
                "This report is generated locally. Full pass/fail values are "
                "populated by the surrounding Make targets and test artifacts.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_DIR / 'final-readiness-report.json'}")
    print(f"Wrote {OUT_DIR / 'final-readiness-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
