"""Plan output paths for split audio segments."""

from pathlib import Path

from sleepsplit.file_assignment import normalize_filename


def plan_output_paths(
    source_file: str | Path,
    album_name: str,
    segment_count: int,
) -> list[Path]:
    """Plan numbered output paths without creating files or directories."""
    source_path = Path(source_file)

    if source_path.suffix.lower() != ".mp3":
        raise ValueError("source_file must be an MP3 file")

    album_name = album_name.strip()

    if album_name and (
        album_name in {".", ".."} or "/" in album_name or "\\" in album_name
    ):
        raise ValueError("album_name must be a single directory name")

    album_name = normalize_filename(album_name)

    if not isinstance(segment_count, int) or isinstance(segment_count, bool):
        raise TypeError("segment_count must be an integer")

    if segment_count < 1:
        raise ValueError("segment_count must be at least 1")

    output_dir = source_path.parent / (f"{album_name}_cut" if album_name else "cut")
    source_stem = source_path.stem

    return [
        output_dir / f"{source_stem}_{number:03d}.mp3"
        for number in range(1, segment_count + 1)
    ]
