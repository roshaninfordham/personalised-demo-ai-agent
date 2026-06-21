"""Safe JSON cleanup for model responses."""

import re


def strip_json_code_fence(raw: str) -> str:
    value = raw.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", value, re.DOTALL | re.IGNORECASE)
    if match is None:
        return value
    return match.group(1).strip()
