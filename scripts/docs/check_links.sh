#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

root = Path.cwd()
files = [root / "README.md", *sorted((root / "docs").rglob("*.md"))]
link_re = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
failures: list[str] = []

for file_path in files:
    text = file_path.read_text(encoding="utf-8")
    for match in link_re.finditer(text):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        if target_path.startswith("app://"):
            continue
        resolved = (file_path.parent / target_path).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            failures.append(f"{file_path.relative_to(root)}: link escapes repo: {target}")
            continue
        if not resolved.exists():
            failures.append(f"{file_path.relative_to(root)}: missing link target: {target}")

if failures:
    print("Documentation link check failed:")
    for failure in failures:
        print(f"  {failure}")
    sys.exit(1)

print(f"Documentation link check passed for {len(files)} files.")
PY
