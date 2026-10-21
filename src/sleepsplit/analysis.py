"""Coordinate silence detection and cut point selection."""

from pathlib import Path

from sleepsplit.cut_point_selection import select_absolute_cut_point
from sleepsplit.ffmpeg_analysis import detect_silence


def find_next_cut_point(
    audio_file: str | Path,
    segment_start: float,
) -> float | None:
    """Find the next suitable absolute cut point in an audio file."""
    pauses = detect_silence(audio_file)

    return select_absolute_cut_point(
        pauses,
        segment_start=segment_start,
    )


def find_cut_points(audio_file: str | Path) -> list[float]:
    """Find all suitable cut points after analyzing an audio file once.

    Returns:
        Absolute cut positions in seconds, in ascending order.
    """
    pauses = detect_silence(audio_file)
    cut_points: list[float] = []
    segment_start = 0.0

    while True:
        cut_point = select_absolute_cut_point(
            pauses,
            segment_start=segment_start,
        )

        if cut_point is None:
            break

        cut_points.append(cut_point)
        segment_start = cut_point

    return cut_points
