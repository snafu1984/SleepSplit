"""Shared result types for SleepSplit."""

from enum import Enum


class SplitResult(Enum):
    """Outcome of processing an audiobook."""

    SPLIT = "split"
    SKIPPED = "skipped"
