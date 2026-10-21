"""Select absolute cut points from detected silence intervals."""

from sleepsplit.segment_selection import (
    MAX_DURATION,
    MIN_DURATION,
    TARGET_DURATION,
)


def select_absolute_cut_point(
    pauses: list[tuple[float, float]],
    segment_start: float,
) -> float | None:
    """Select an absolute cut point near the target segment duration.

    The midpoint of each silence interval is used as its candidate
    cut point. Only candidates within the allowed segment duration
    range are considered.

    Args:
        pauses: Silence intervals as absolute (start, end) times in seconds.
        segment_start: Absolute start time of the current segment in seconds.

    Returns:
        The selected absolute cut time, or None if no suitable pause exists.
        Ties are resolved in favor of the earlier cut point.
    """
    candidates = [
        (start + end) / 2 for start, end in pauses if start >= 0 and end > start
    ]

    relative_candidates = [
        candidate
        for candidate in candidates
        if MIN_DURATION <= candidate - segment_start <= MAX_DURATION
    ]

    if not relative_candidates:
        return None

    selected = min(
        relative_candidates,
        key=lambda candidate: (
            abs((candidate - segment_start) - TARGET_DURATION),
            candidate,
        ),
    )

    return selected
