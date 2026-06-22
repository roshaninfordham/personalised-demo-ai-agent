from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from pathlib import Path

SCAN_ROOTS = (
    Path("tests/fixtures"),
    Path("tests/evals"),
    Path("tests/e2e/fixtures"),
    Path("tests/load"),
)

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("api_key", re.compile(r"api[_-]?key", re.IGNORECASE)),
    ("secret", re.compile(r"secret", re.IGNORECASE)),
    ("token", re.compile(r"token", re.IGNORECASE)),
    ("password", re.compile(r"password", re.IGNORECASE)),
    ("private_key", re.compile(r"private[_-]?key", re.IGNORECASE)),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{10,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{12,}")),
    ("nvidia_key", re.compile(r"nvapi-[A-Za-z0-9_-]{12,}", re.IGNORECASE)),
    ("aws_access_key", re.compile(r"AWS_ACCESS_KEY", re.IGNORECASE)),
)

ALLOWLIST_PATTERNS = (
    re.compile(r"fake_[A-Za-z0-9_:-]+"),
    re.compile(r"token_type", re.IGNORECASE),
    re.compile(r"fixture_secret_scanner_allowlist", re.IGNORECASE),
)

TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".ts",
    ".tsx",
    ".js",
    ".py",
    ".html",
    ".css",
    ".csv",
}


def main() -> int:
    findings: list[str] = []
    for path in _iter_files(SCAN_ROOTS):
        text = path.read_text(errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if _is_allowlisted(line):
                continue
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{path}:{line_number}: possible {name}")
    if findings:
        print("Secret-like content found in test fixtures:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 1
    print("No real secret-like fixture content found.")
    return 0


def _iter_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in TEXT_SUFFIXES:
                yield path


def _is_allowlisted(line: str) -> bool:
    return any(pattern.search(line) for pattern in ALLOWLIST_PATTERNS)


if __name__ == "__main__":
    raise SystemExit(main())
