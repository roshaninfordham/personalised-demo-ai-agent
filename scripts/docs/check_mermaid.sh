#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from __future__ import annotations

from pathlib import Path

root = Path.cwd()
count = 0
for file_path in [root / "README.md", *sorted((root / "docs").rglob("*.md"))]:
    in_block = False
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "```mermaid":
            in_block = True
            count += 1
        elif in_block and line.strip() == "```":
            in_block = False

print(f"Found {count} Mermaid diagrams.")
if count < 6:
    raise SystemExit("Expected at least 6 Mermaid diagrams.")
PY

if command -v mmdc >/dev/null 2>&1; then
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT
  python3 - "$tmpdir" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

root = Path.cwd()
out = Path(sys.argv[1])
idx = 0
for file_path in [root / "README.md", *sorted((root / "docs").rglob("*.md"))]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    in_block = False
    block: list[str] = []
    for line in lines:
        if line.strip() == "```mermaid":
            in_block = True
            block = []
            continue
        if in_block and line.strip() == "```":
            (out / f"diagram_{idx}.mmd").write_text("\n".join(block) + "\n", encoding="utf-8")
            idx += 1
            in_block = False
            continue
        if in_block:
            block.append(line)
print(idx)
PY
  for diagram in "$tmpdir"/*.mmd; do
    mmdc -i "$diagram" -o "$diagram.svg" >/dev/null
  done
  echo "Mermaid CLI validation passed."
else
  echo "Mermaid CLI 'mmdc' not found; syntax rendering skipped locally."
fi
