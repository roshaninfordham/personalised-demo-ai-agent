#!/usr/bin/env python3
"""Validate provisioned Grafana dashboard JSON files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_DASHBOARDS = {
    "realtime-ux.json",
    "browser-reliability.json",
    "agent-quality.json",
    "infrastructure-health.json",
    "cost-usage.json",
    "session-debug.json",
    "latency-budget.json",
}


def main() -> int:
    root = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("infra/observability/grafana/dashboards")
    )
    missing = REQUIRED_DASHBOARDS - {path.name for path in root.glob("*.json")}
    if missing:
        print(f"Missing dashboards: {sorted(missing)}", file=sys.stderr)
        return 1
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text())
        panels = payload.get("panels")
        if not isinstance(panels, list) or not panels:
            print(f"{path}: dashboard has no panels", file=sys.stderr)
            return 1
        text = json.dumps(payload)
        if "session_id" in text and "session-debug" not in path.name:
            print(f"{path}: dashboard must not query session_id metric labels", file=sys.stderr)
            return 1
        if path.name != "session-debug.json" and "live_demo_" not in text:
            print(f"{path}: no live_demo metric references", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
