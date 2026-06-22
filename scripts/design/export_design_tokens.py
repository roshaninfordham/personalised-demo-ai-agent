#!/usr/bin/env python3
"""Export DESIGN.md tokens for the Next.js app.

The upstream alpha CLI emits Tailwind v4 `@theme` CSS. The app also needs runtime
CSS variables, so this script preserves the CLI output and appends stable aliases
used by `globals.css`.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "apps/web/app/design-tokens.css"

ALIASES = {
    "--bg": "--color-background",
    "--surface": "--color-surface",
    "--surface-elevated": "--color-surfaceElevated",
    "--border": "--color-border",
    "--text": "--color-textPrimary",
    "--muted": "--color-textSecondary",
    "--accent": "--color-primary",
    "--accent-strong": "--color-primaryHover",
    "--danger": "--color-danger",
    "--warning": "--color-warning",
    "--success": "--color-success",
    "--space-xs": "--spacing-xs",
    "--space-sm": "--spacing-sm",
    "--space-md": "--spacing-md",
    "--space-lg": "--spacing-lg",
    "--space-xl": "--spacing-xl",
}


def main() -> int:
    npx = shutil.which("npx")
    if npx is None:
        raise RuntimeError("npx is required to export DESIGN.md tokens.")
    result = subprocess.run(  # noqa: S603
        [
            npx,
            "@google/design.md",
            "export",
            "--format",
            "css-tailwind",
            "DESIGN.md",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    token_values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped.startswith("--") or ":" not in stripped:
            continue
        key, value = stripped.rstrip(";").split(":", 1)
        token_values[key.strip()] = value.strip()
    root_lines = ["", ":root {"]
    for key, value in token_values.items():
        root_lines.append(f"  {key}: {value};")
    root_lines.append("  --surface-muted: #172033;")
    root_lines.append("  --focus: #93c5fd;")
    root_lines.append(
        "  --font-sans: Inter, ui-sans-serif, system-ui, -apple-system, "
        'BlinkMacSystemFont, "Segoe UI", sans-serif;'
    )
    for alias, source in ALIASES.items():
        root_lines.append(f"  {alias}: var({source});")
    root_lines.append("}")
    token_css = result.stdout.rstrip() + "\n" + "\n".join(root_lines) + "\n"
    OUTPUT.write_text(token_css, encoding="utf-8")
    print(f"Exported design tokens to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
