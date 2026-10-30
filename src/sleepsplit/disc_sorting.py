"""Sort MP3 files by ID3 disc number and create M3U playlists."""

import re
import shutil
from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError

DISC_PATTERN = re.compile(r"(\d+)(?:/\d+)?")


def get_disc_number(path: Path) -> int | None:
    """Read and validate the ID3 TPOS disc number."""
    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        return None

    frames = tags.getall("TPOS")

    if not frames or not frames[0].text:
        return None

    value = str(frames[0].text[0]).strip()
    match = re.fullmatch(DISC_PATTERN, value)

    if not match:
        return None

    disc_number = int(match.group(1))

    return disc_number if disc_number >= 1 else None


def get_mp3_files(directory: Path) -> list[Path]:
    """Return top-level MP3 files in case-insensitive filename order."""
    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() == ".mp3"
        ),
        key=lambda path: path.name.casefold(),
    )


def get_cd_directories(root: Path) -> list[Path]:
    """Return existing CD directories."""
    return sorted(
        (
            path
            for path in root.iterdir()
            if path.is_dir() and re.fullmatch(r"CD\d+", path.name, re.IGNORECASE)
        ),
        key=lambda path: path.name.casefold(),
    )


def plan_disc_sorting(
    root: Path,
) -> tuple[list[tuple[Path, Path]], list[str], set[Path]]:
    """Plan file moves and identify directories needing playlists."""
    planned_moves: list[tuple[Path, Path]] = []
    warnings: list[str] = []
    affected_directories = set(get_cd_directories(root))
    planned_targets: set[str] = set()

    for source in get_mp3_files(root):
        disc_number = get_disc_number(source)

        if disc_number is None:
            warnings.append(f"Missing or invalid TPOS tag, skipping: {source.name}")
            continue

        folder = root / f"CD{disc_number:02d}"
        destination = folder / source.name
        target_key = str(destination).casefold()

        if destination.exists() or target_key in planned_targets:
            warnings.append(f"Destination already exists, skipping: {destination}")
            continue

        planned_targets.add(target_key)
        planned_moves.append((source, destination))
        affected_directories.add(folder)

    return planned_moves, warnings, affected_directories


def create_playlist(folder: Path) -> int:
    """Create an M3U playlist for all MP3 files in a CD directory."""
    files = get_mp3_files(folder)
    playlist = folder / f"{folder.name}.m3u"

    with playlist.open(
        "w",
        encoding="utf-8-sig",
        newline="\n",
    ) as file:
        file.write("#EXTM3U\n")

        for path in files:
            file.write(f"{path.name}\n")

    return len(files)


def sort_files_by_disc(
    root: Path,
) -> tuple[list[tuple[Path, Path]], list[str], dict[Path, int]]:
    """Move MP3 files into CD directories and create their playlists."""
    planned_moves, warnings, affected_directories = plan_disc_sorting(root)
    moved_files: list[tuple[Path, Path]] = []

    for source, destination in planned_moves:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Check again immediately before moving.
            if destination.exists():
                warnings.append(f"Destination already exists, skipping: {destination}")
                continue

            shutil.move(str(source), str(destination))
            moved_files.append((source, destination))

        except OSError as exc:
            warnings.append(f"Could not move {source.name}: {exc}")

    playlist_counts: dict[Path, int] = {}

    for folder in sorted(
        affected_directories,
        key=lambda path: path.name.casefold(),
    ):
        if not folder.is_dir():
            continue

        try:
            playlist_counts[folder] = create_playlist(folder)
        except OSError as exc:
            warnings.append(f"Could not create playlist in {folder.name}: {exc}")

    return moved_files, warnings, playlist_counts
