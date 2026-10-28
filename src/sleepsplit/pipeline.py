"""Coordinate the audiobook splitting workflow."""

import math
from pathlib import Path

from sleepsplit.analysis import plan_cut_points
from sleepsplit.audio_metadata import get_album_name, get_audio_duration
from sleepsplit.ffmpeg_analysis import detect_silence
from sleepsplit.output_planning import plan_output_paths
from sleepsplit.splitting import split_audio


def _check_output_paths(output_paths: list[Path]) -> None:
    """Raise an error if any planned output file already exists."""
    existing_paths = [path for path in output_paths if path.exists()]

    if existing_paths:
        names = ", ".join(path.name for path in existing_paths)
        raise FileExistsError(f"Output file(s) already exist: {names}")


def split_audiobook(source_file: str | Path) -> None:
    """Split an audiobook at suitable pauses.

    If no suitable cut points are found, leave the source file untouched
    and do not create output files or directories.
    """
    duration = get_audio_duration(source_file)

    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Audio duration must be finite and greater than zero.")

    pauses = detect_silence(source_file)
    cut_points = plan_cut_points(pauses, audio_duration=duration)

    if not cut_points:
        return

    album_name = get_album_name(source_file)
    output_paths = plan_output_paths(
        source_file,
        album_name,
        segment_count=len(cut_points) + 1,
    )

    _check_output_paths(output_paths)
    split_audio(source_file, cut_points, output_paths)
