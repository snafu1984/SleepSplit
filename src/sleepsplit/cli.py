"""Command-line interface for SleepSplit."""

import argparse
import sys
from pathlib import Path

from sleepsplit.models import SplitResult
from sleepsplit.pipeline import split_audiobook


def main() -> int:
    """Run SleepSplit on all MP3 files in one directory."""
    parser = argparse.ArgumentParser(
        prog="sleepsplit",
        description=(
            "Split MP3 audiobooks in the specified directory. "
            "Subdirectories are not searched."
        ),
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing MP3 files to process.",
    )
    args = parser.parse_args()

    directory = args.directory.expanduser()

    if not directory.exists():
        parser.error(f"Directory does not exist: {directory}")

    if not directory.is_dir():
        parser.error(f"Path is not a directory: {directory}")

    mp3_files = sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() == ".mp3"
        ),
        key=lambda path: path.name.casefold(),
    )

    if not mp3_files:
        print(f"No MP3 files found in: {directory}")
        return 0

    split_count = 0
    skipped_count = 0
    failed_count = 0

    for source_file in mp3_files:
        print(f"\nProcessing: {source_file.name}")

        try:
            result = split_audiobook(source_file)
        except (OSError, RuntimeError, ValueError) as exc:
            failed_count += 1
            print(
                f"ERROR: {source_file.name}: {exc}",
                file=sys.stderr,
            )
            continue

        if result is SplitResult.SPLIT:
            split_count += 1
            print(f"Split successfully: {source_file.name}")
        elif result is SplitResult.SKIPPED:
            skipped_count += 1
            print(f"Skipped (no suitable cut points): {source_file.name}")
        else:
            failed_count += 1
            print(
                f"ERROR: Unexpected result for {source_file.name}: {result!r}",
                file=sys.stderr,
            )

    print("\nSummary")
    print(f"Split successfully: {split_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Failed: {failed_count}")
    print(f"Total: {len(mp3_files)}")

    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
