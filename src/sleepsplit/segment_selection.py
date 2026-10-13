"""Select suitable cut points for audiobook segments."""

TARGET_DURATION = 300
MIN_DURATION = 240
MAX_DURATION = 420


def select_cut_point(
    pause_positions: list[int | float],
) -> int | float | None:
    """Select the pause closest to the target duration.

    Only pauses within the allowed duration range are considered.
    If two pauses are equally close to the target, the earlier
    pause is selected.

    Args:
        pause_positions: Pause positions in seconds relative
            to the beginning of the current segment.

    Returns:
        The selected pause position in seconds, or None if no
        suitable pause exists.
    """
    suitable_pauses = [
        position
        for position in pause_positions
        if MIN_DURATION <= position <= MAX_DURATION
    ]

    if not suitable_pauses:
        return None

    return min(
        suitable_pauses,
        key=lambda position: (abs(position - TARGET_DURATION), position),
    )
