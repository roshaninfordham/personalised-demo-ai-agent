from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {"eval_id", "category", "product_fixture", "user_turns", "expected"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    args = parser.parse_args()
    path = Path(args.dataset)
    files = sorted(path.glob("*.jsonl")) if path.is_dir() else [path]
    case_count = 0
    for file_path in files:
        for line_number, line in enumerate(file_path.read_text().splitlines(), start=1):
            if not line.strip():
                continue
            parsed = json.loads(line)
            if not isinstance(parsed, dict):
                raise ValueError(f"{file_path}:{line_number} must be a JSON object")
            missing = REQUIRED_FIELDS - set(parsed)
            if missing:
                raise ValueError(f"{file_path}:{line_number} missing {sorted(missing)}")
            if not isinstance(parsed["user_turns"], list):
                raise ValueError(f"{file_path}:{line_number} user_turns must be a list")
            if not isinstance(parsed["expected"], dict):
                raise ValueError(f"{file_path}:{line_number} expected must be an object")
            _ensure_no_raw_secret_strings(parsed, file_path=file_path, line_number=line_number)
            case_count += 1
    print(f"Validated {case_count} eval cases from {len(files)} file(s).")
    return 0


def _ensure_no_raw_secret_strings(value: Any, *, file_path: Path, line_number: int) -> None:
    text = json.dumps(value, sort_keys=True)
    forbidden = ("Bearer ", "sk-", "nvapi-", "AWS_ACCESS_KEY")
    for marker in forbidden:
        if marker in text:
            raise ValueError(f"{file_path}:{line_number} contains forbidden marker {marker!r}")


if __name__ == "__main__":
    raise SystemExit(main())
