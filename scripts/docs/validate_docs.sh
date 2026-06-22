#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

root = Path.cwd()
files = [root / "README.md", *sorted((root / "docs").rglob("*.md"))]
failures: list[str] = []

for file_path in files:
    text = file_path.read_text(encoding="utf-8")
    rel = file_path.relative_to(root)
    if not text.endswith("\n"):
        failures.append(f"{rel}: file must end with newline")
    for idx, line in enumerate(text.splitlines(), start=1):
        if line.rstrip() != line:
            failures.append(f"{rel}:{idx}: trailing whitespace")
        if line.startswith("#") and not line.startswith("# "):
            prefix = line.split(" ", 1)[0]
            if any(ch != "#" for ch in prefix) or " " not in line:
                failures.append(f"{rel}:{idx}: malformed heading")
    if text.count("```") % 2 != 0:
        failures.append(f"{rel}: unbalanced fenced code blocks")
    if "# " not in text:
        failures.append(f"{rel}: missing top-level heading")

if failures:
    print("Documentation validation failed:")
    for failure in failures:
        print(f"  {failure}")
    sys.exit(1)

print(f"Documentation validation passed for {len(files)} files.")
PY
