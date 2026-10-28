"""Shared result types and planning models for SleepSplit."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SplitResult(Enum):
    """Outcome of processing an audiobook."""

    SPLIT = "split"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class AudiobookPlan:
    """Planned cuts and output files for one audiobook."""

    cut_points: list[float]
    output_paths: list[Path]
