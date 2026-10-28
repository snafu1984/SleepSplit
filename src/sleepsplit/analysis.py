"""Coordinate silence detection and cut point selection."""

import math
from pathlib import Path

from sleepsplit.cut_point_selection import select_absolute_cut_point
from sleepsplit.ffmpeg_analysis import detect_silence
from sleepsplit.segment_selection import (
    MAX_DURATION,
    MIN_DURATION,
    TARGET_DURATION,
)


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


def plan_cut_points(
    pauses: list[tuple[float, float]],
    audio_duration: float,
) -> list[float]:
    """Plan cut points, allowing a short final segment if necessary.

    First searches for a plan where every segment is within the
    allowed duration range. If no such plan exists, chooses a plan
    whose non-final segments are valid and whose final segment is
    as close as possible to the allowed range.

    Args:
        pauses: Absolute silence intervals as (start, end) pairs.
        audio_duration: Total audio duration in seconds.

    Returns:
        Absolute cut positions in ascending order.
    """
    if not math.isfinite(audio_duration) or audio_duration <= 0:
        raise ValueError("audio_duration must be finite and greater than zero.")
    candidates = sorted(
        {
            (start + end) / 2
            for start, end in pauses
            if start >= 0 and end > start and start < audio_duration
        }
    )

    if audio_duration <= MAX_DURATION:
        return []

    # Each entry stores the lowest cost and cut sequence reaching a pause.
    best: dict[float, tuple[float, list[float]]] = {0.0: (0.0, [])}

    for candidate in candidates:
        possible_previous = [
            (position, result)
            for position, result in best.items()
            if MIN_DURATION <= candidate - position <= MAX_DURATION
        ]

        if possible_previous:
            previous_position, (previous_cost, previous_cuts) = min(
                possible_previous,
                key=lambda item: (
                    item[1][0] + abs((candidate - item[0]) - TARGET_DURATION),
                    item[0],
                ),
            )
            best[candidate] = (
                previous_cost + abs((candidate - previous_position) - TARGET_DURATION),
                [*previous_cuts, candidate],
            )

    # Prefer a fully valid plan, including the final segment.
    final_min_duration = 120.0
    final_max_duration = 540.0

    complete_paths = [
        (cost, cuts)
        for position, (cost, cuts) in best.items()
        if cuts
        and final_min_duration <= audio_duration - position <= final_max_duration
    ]

    if complete_paths:
        _, selected_cuts = min(
            complete_paths,
            key=lambda item: (item[0], len(item[1])),
        )
        return selected_cuts

    return []
