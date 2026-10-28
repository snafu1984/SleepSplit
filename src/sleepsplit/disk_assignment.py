"""Assign split MP3 files to discs and write ID3 TPOS tags."""

import math
from pathlib import Path

from mutagen.id3 import ID3, TPOS, ID3NoHeaderError
from mutagen.mp3 import MP3

MIN_DISC_SECONDS = 55 * 60
TARGET_DISC_SECONDS = 60 * 60
MAX_DISC_SECONDS = 65 * 60


def _plan_disc_groups(durations: list[float]) -> list[int]:
    """Assign consecutive segments to discs targeting 60 minutes.

    Regular discs must be 55–65 minutes long.
    The final disc may be shorter than 55 minutes.
    """
    if not durations:
        return []

    if any(not math.isfinite(duration) or duration <= 0 for duration in durations):
        raise ValueError("Segment durations must be finite and greater than zero.")

    if any(duration > MAX_DISC_SECONDS for duration in durations):
        raise ValueError("A segment exceeds 65 minutes and cannot fit on a disc.")

    count = len(durations)

    # Dynamic programming for regular discs.
    best: list[tuple[int, float] | None] = [None] * (count + 1)
    previous_index = [-1] * (count + 1)
    best[0] = (0, 0.0)

    for end in range(1, count + 1):
        total = 0.0

        for start in range(end - 1, -1, -1):
            total += durations[start]

            if total > MAX_DISC_SECONDS:
                break
            if total < MIN_DISC_SECONDS or best[start] is None:
                continue

            previous_count, previous_cost = best[start]
            candidate = (
                previous_count + 1,
                previous_cost + (total - TARGET_DISC_SECONDS) ** 2,
            )

            current = best[end]
            if (
                current is None
                or candidate[0] < current[0]
                or (candidate[0] == current[0] and candidate[1] < current[1])
            ):
                best[end] = candidate
                previous_index[end] = start

    # Evaluate each possible final disc. Prefer a shorter final disc
    # when the number and quality of regular discs are equal.
    best_key: tuple[int, float, float] | None = None
    best_start = -1
    total = 0.0

    for start in range(count - 1, -1, -1):
        total += durations[start]

        if total > MAX_DISC_SECONDS:
            break

        if start == 0:
            regular_count, regular_cost = 0, 0.0
        else:
            if best[start] is None:
                continue
            regular_count, regular_cost = best[start]

        key = (
            regular_count,
            regular_cost,
            total,
        )

        if best_key is None or key < best_key:
            best_key = key
            best_start = start

    if best_start < 0:
        raise ValueError(
            "Cannot assign segments to discs with the 55–65 minute "
            "duration rule. Try different segment lengths."
        )

    groups: list[tuple[int, int]] = []
    end = best_start

    while end > 0:
        start = previous_index[end]
        if start < 0:
            raise ValueError("Could not reconstruct the disc assignment.")
        groups.append((start, end))
        end = start

    groups.reverse()
    groups.append((best_start, count))

    disc_numbers = [0] * count
    for disc_number, (start, end) in enumerate(groups, start=1):
        for index in range(start, end):
            disc_numbers[index] = disc_number

    return disc_numbers


def assign_disc_tags(output_paths: list[Path]) -> None:
    """Assign disc numbers based on segment durations and write TPOS tags."""
    if not output_paths:
        return

    durations = [float(MP3(path).info.length) for path in output_paths]
    disc_numbers = _plan_disc_groups(durations)
    total_discs = max(disc_numbers)

    # Calculate the complete assignment before modifying any tags.
    for path, disc_number in zip(output_paths, disc_numbers, strict=True):
        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()

        tags.delall("TPOS")
        tags.add(
            TPOS(
                encoding=3,
                text=[f"{disc_number:02d}/{total_discs:02d}"],
            )
        )
        tags.save(path)
