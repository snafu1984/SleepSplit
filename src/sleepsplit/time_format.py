"""Convert time values to the mp3splt time format."""

from decimal import ROUND_HALF_UP, Decimal


def seconds_to_mp3splt_time(seconds: float) -> str:
    """Convert seconds to mp3splt's min.sec[.hundredths] format.

    Values are rounded to hundredths of a second. If rounding
    crosses a minute boundary, the result is normalized.

    Args:
        seconds: A non-negative duration in seconds.

    Returns:
        The duration in mp3splt time format.

    Raises:
        ValueError: If seconds is negative.
    """
    if seconds < 0:
        raise ValueError("Seconds must not be negative.")

    total_hundredths = int(
        (Decimal(str(seconds)) * 100).quantize(
            Decimal(1),
            rounding=ROUND_HALF_UP,
        )
    )

    total_seconds, hundredths = divmod(total_hundredths, 100)
    minutes, remaining_seconds = divmod(total_seconds, 60)

    if hundredths:
        return f"{minutes}.{remaining_seconds:02d}.{hundredths:02d}"

    return f"{minutes}.{remaining_seconds:02d}"
