"""Coordinate the audiobook splitting workflow."""

import math
import shutil
from pathlib import Path

from sleepsplit.analysis import plan_cut_points
from sleepsplit.audio_metadata import get_album_name, get_audio_duration
from sleepsplit.disk_assignment import assign_disc_tags
from sleepsplit.ffmpeg_analysis import detect_silence
from sleepsplit.models import AudiobookPlan, SplitResult
from sleepsplit.output_planning import plan_output_paths
from sleepsplit.splitting import split_audio


def _check_output_paths(output_paths: list[Path]) -> None:
    """Raise an error if any planned output file already exists."""
    existing_paths = [path for path in output_paths if path.exists()]

    if existing_paths:
        names = ", ".join(path.name for path in existing_paths)
        raise FileExistsError(f"Output file(s) already exist: {names}")


def plan_audiobook(source_file: str | Path) -> AudiobookPlan | None:
    """Analyze an audiobook and plan its cuts and output files.

    Return None when no suitable cut points are found.
    Do not create or modify any files.
    """
    source_file = Path(source_file)
    duration = get_audio_duration(source_file)

    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Audio duration must be finite and greater than zero.")

    pauses = detect_silence(source_file)
    cut_points = plan_cut_points(pauses, audio_duration=duration)

    if not cut_points:
        return None

    album_name = get_album_name(source_file)
    output_paths = plan_output_paths(
        source_file,
        album_name,
        segment_count=len(cut_points) + 1,
    )

    return AudiobookPlan(
        cut_points=cut_points,
        output_paths=output_paths,
    )


def _copy_unsplittable_audiobook(
    source_file: Path,
    *,
    dry_run: bool = False,
) -> None:
    """Copy an audiobook without suitable cuts to its output directory."""
    album_name = get_album_name(source_file).strip()
    output_dir = source_file.parent / (f"{album_name}_cut" if album_name else "cut")
    output_file = output_dir / source_file.name

    if output_file.exists():
        raise FileExistsError(f"Output file already exists: {output_file.name}")

    if dry_run:
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, output_file)


def split_audiobook(
    source_file: str | Path,
    *,
    dry_run: bool = False,
    disk: bool = False,
) -> SplitResult:
    """Split an audiobook, or only plan the split in dry-run mode.

    Return SPLIT when a valid split plan exists.
    Return SKIPPED when no suitable cut points are found.

    Dry-run mode does not create or modify files.
    """
    plan = plan_audiobook(source_file)

    if plan is None:
        _copy_unsplittable_audiobook(
            Path(source_file),
            dry_run=dry_run,
        )
        return SplitResult.SKIPPED

    if dry_run:
        return SplitResult.SPLIT

    _check_output_paths(plan.output_paths)
    split_audio(source_file, plan.cut_points, plan.output_paths)

    if disk:
        assign_disc_tags(plan.output_paths)

    return SplitResult.SPLIT
