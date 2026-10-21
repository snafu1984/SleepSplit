"""Parse silence intervals reported by FFmpeg."""

import re

SILENCE_START_PATTERN = re.compile(r"silence_start:\s*(-?\d+(?:\.\d+)?)")
SILENCE_END_PATTERN = re.compile(r"silence_end:\s*(-?\d+(?:\.\d+)?)")


def parse_silence_output(output: str) -> list[tuple[float, float]]:
    """Parse complete, valid silence intervals from FFmpeg output.

    Args:
        output: Combined text output containing FFmpeg messages.

    Returns:
        Valid silence intervals as (start, end) pairs in seconds.
        Incomplete or invalid intervals are ignored.
    """
    intervals: list[tuple[float, float]] = []
    pending_start: float | None = None

    for line in output.splitlines():
        start_match = SILENCE_START_PATTERN.search(line)
        if start_match:
            start = float(start_match.group(1))
            pending_start = start if start >= 0 else None
            continue

        end_match = SILENCE_END_PATTERN.search(line)
        if end_match and pending_start is not None:
            end = float(end_match.group(1))

            if end > pending_start:
                intervals.append((pending_start, end))

            pending_start = None

    return intervals
