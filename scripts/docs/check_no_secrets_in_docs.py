#!/usr/bin/env python3
"""Fail if documentation contains obvious real secret patterns."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_PATHS = [ROOT / "README.md", ROOT / "docs"]

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("nvidia_key", re.compile(r"nvapi-[A-Za-z0-9_-]{16,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"BEGIN (RSA |EC |OPENSSH |)?PRIVATE KEY")),
    ("auth_header", re.compile(r"Authorization:\s+[A-Za-z]+")),
    (
        "database_url_real",
        re.compile(
            r"DATABASE_URL=postgres(?:ql)?://"
            r"(?!.*(?:example|REPLACE_ME|fake_|localhost))",
            re.IGNORECASE,
        ),
    ),
    (
        "jwt_secret_real",
        re.compile(
            r"JWT_SECRET=(?!<|REPLACE_ME|fake_|replace-with|example)[^\s]+",
            re.IGNORECASE,
        ),
    ),
    (
        "session_secret_real",
        re.compile(
            r"SESSION_SECRET=(?!<|REPLACE_ME|fake_|replace-with|example)[^\s]+",
            re.IGNORECASE,
        ),
    ),
]


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in DOC_PATHS:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
    return files


def main() -> int:
    failures: list[str] = []
    for file_path in iter_markdown_files():
        text = file_path.read_text(encoding="utf-8")
        for name, pattern in PATTERNS:
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                failures.append(f"{file_path.relative_to(ROOT)}:{line_no}: possible {name}")

    if failures:
        print("Documentation secret scan failed:")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(f"Documentation secret scan passed for {len(iter_markdown_files())} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
