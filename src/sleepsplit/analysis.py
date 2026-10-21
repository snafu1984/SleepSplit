"""Coordinate silence detection and cut point selection."""

from pathlib import Path

from sleepsplit.cut_point_selection import select_absolute_cut_point
from sleepsplit.ffmpeg_analysis import detect_silence


def find_next_cut_point(
    audio_file: str | Path,
    segment_start: float,
) -> float | None:
    """Find the next suitable absolute cut point in an audio file.

    Args:
        audio_file: Path to the audio file to analyze.
        segment_start: Absolute start time of the current segment in seconds.

    Returns:
        The absolute cut time in seconds, or None if no suitable pause exists.
    """
    pauses = detect_silence(audio_file)

    return select_absolute_cut_point(
        pauses,
        segment_start=segment_start,
    )
