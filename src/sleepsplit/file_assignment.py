"""Rename MP3 files using their ID3 TIT2 title tags."""

import re
from pathlib import Path

from mutagen.id3 import ID3, ID3NoHeaderError


def normalize_filename(title: str) -> str:
    """Normalize a title for use as a Linux/macOS filename."""
    replacements = {
        "ä": "ae",
        "Ä": "Ae",
        "ö": "oe",
        "Ö": "Oe",
        "ü": "ue",
        "Ü": "Ue",
        "ß": "ss",
    }

    for character, replacement in replacements.items():
        title = title.replace(character, replacement)

    title = re.sub(r"[^A-Za-z0-9-]", "_", title)
    title = re.sub(r"_+", "_", title)

    return title.strip("_")


def plan_file_renames(
    output_paths: list[Path],
) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Create a safe rename plan based on ID3 TIT2 tags."""
    rename_plan: list[tuple[Path, Path]] = []
    warnings: list[str] = []
    planned_targets: set[str] = set()

    ordered_paths = sorted(
        output_paths,
        key=lambda path: path.name.casefold(),
    )

    for path in ordered_paths:
        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            warnings.append(f"No TIT2 tag found: {path.name}")
            continue

        title_tag = tags.get("TIT2")

        if not title_tag or not title_tag.text:
            warnings.append(f"No TIT2 title found: {path.name}")
            continue

        title = str(title_tag.text[0]).strip()
        filename = normalize_filename(title)

        if not filename:
            warnings.append(f"Empty filename after normalization: {path.name}")
            continue

        target = path.with_name(f"{filename}.mp3")

        # Nothing to do if the filename is already correct.
        if target.name.casefold() == path.name.casefold():
            continue

        target_key = str(target.parent).casefold() + "/" + target.name.casefold()

        # Never overwrite an existing file or another planned destination.
        if target.exists() or target_key in planned_targets:
            warnings.append(f"Filename already exists, skipping: {target.name}")
            continue

        planned_targets.add(target_key)
        rename_plan.append((path, target))

    return rename_plan, warnings


def rename_files_from_titles(
    output_paths: list[Path],
) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Rename MP3 files using their normalized ID3 TIT2 titles."""
    rename_plan, warnings = plan_file_renames(output_paths)
    renamed_files: list[tuple[Path, Path]] = []

    for source, target in rename_plan:
        try:
            # Check again immediately before renaming.
            if target.exists():
                warnings.append(f"Filename already exists, skipping: {target.name}")
                continue

            source.rename(target)
            renamed_files.append((source, target))

        except OSError as exc:
            warnings.append(f"Could not rename {source.name}: {exc}")

    return renamed_files, warnings
