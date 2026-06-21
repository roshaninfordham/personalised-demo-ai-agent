"""Demo planner phases."""

from enum import StrEnum


class DemoPhase(StrEnum):
    START = "START"
    DISCOVERY = "DISCOVERY"
    OVERVIEW = "OVERVIEW"
    CORE_WORKFLOW = "CORE_WORKFLOW"
    DEEP_DIVE = "DEEP_DIVE"
    Q_AND_A = "Q_AND_A"
    SUMMARY = "SUMMARY"
    END = "END"
    RECOVERY = "RECOVERY"
