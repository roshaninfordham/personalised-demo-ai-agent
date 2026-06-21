"""Pipecat frame type mapping boundary.

Pipecat is not imported outside this package. When the dependency is added,
version-specific frame inspection belongs here.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NormalizedTextFrame:
    text: str
    is_final: bool
    speaker: str
