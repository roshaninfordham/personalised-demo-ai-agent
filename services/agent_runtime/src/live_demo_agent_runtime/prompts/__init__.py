"""Prompt file helpers."""

from pathlib import Path


def prompt_path(name: str) -> Path:
    return Path(__file__).parent / name
