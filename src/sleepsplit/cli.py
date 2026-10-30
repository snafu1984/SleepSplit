"""Command-line interface for SleepSplit."""

import argparse
import sys
from pathlib import Path

from sleepsplit.audio_metadata import get_album_name
from sleepsplit.disk_assignment import assign_disc_tags
from sleepsplit.models import SplitResult
from sleepsplit.pipeline import plan_audiobook, split_audiobook
from sleepsplit.track_assignment import assign_track_tags


def _print_summary(
    split_count: int,
    skipped_count: int,
    failed_count: int,
    total_count: int,
    *,
    dry_run: bool = False,
) -> None:
    """Print a summary of the audiobook processing results."""
    title = "Dry-run summary" if dry_run else "SleepSplit summary"
    split_label = "Would split:" if dry_run else "Split successfully:"

    print(f"\n{'=' * 50}")
    print(title)
    print(f"{'=' * 50}")
    print(f"{split_label:<22}{split_count:>5}")
    print(f"{'Skipped:':<22}{skipped_count:>5}")
    print(f"{'Failed:':<22}{failed_count:>5}")
    print(f"{'Total:':<22}{total_count:>5}")
    print(f"{'=' * 50}")


def _get_output_dir(source_file: Path) -> Path:
    """Return the output directory for an audiobook."""
    album_name = get_album_name(source_file).strip()
    return source_file.parent / (f"{album_name}_cut" if album_name else "cut")


def _get_mp3_files(directory: Path) -> list[Path]:
    """Return top-level MP3 files in case-insensitive filename order."""
    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() == ".mp3"
        ),
        key=lambda path: path.name.casefold(),
    )


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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze files and show the planned outputs without modifying files.",
    )
    parser.add_argument(
        "--disk",
        action="store_true",
        help="Assign disc numbers to output MP3 files using ID3 TPOS tags.",
    )
    parser.add_argument(
        "--track",
        action="store_true",
        help="Assign track numbers to output MP3 files using ID3 TRCK tags.",
    )
    args = parser.parse_args()

    directory = args.directory.expanduser()

    if not directory.exists():
        parser.error(f"Directory does not exist: {directory}")

    if not directory.is_dir():
        parser.error(f"Path is not a directory: {directory}")

    mp3_files = _get_mp3_files(directory)

    if not mp3_files:
        print(f"No MP3 files found in: {directory}")
        return 0

    if args.dry_run:
        print("DRY RUN: No files will be created or modified.")

    split_count = 0
    skipped_count = 0
    failed_count = 0

    # Collect output directories for metadata assignment after processing.
    output_dirs: set[Path] = set()

    for source_file in mp3_files:
        print(f"\nProcessing: {source_file.name}")

        try:
            if args.dry_run:
                plan = plan_audiobook(source_file)

            if args.dry_run:
                plan = plan_audiobook(source_file)

                if plan is None:
                    result = SplitResult.SKIPPED

                    if args.disk or args.track:
                        output_dir = _get_output_dir(source_file)
                        output_dirs.add(output_dir)
                        print(f"  Planned copied file: {output_dir / source_file.name}")
                else:
                    result = SplitResult.SPLIT
                    output_dir = plan.output_paths[0].parent

                    if args.disk or args.track:
                        output_dirs.add(output_dir)

                    print(f"  Planned cuts: {len(plan.cut_points)}")

                    for index, cut_point in enumerate(
                        plan.cut_points,
                        start=1,
                    ):
                        print(f"  Cut {index}: {cut_point:.2f} seconds")

                    print("  Planned output files:")
                    for output_path in plan.output_paths:
                        print(f"    {output_path}")

            else:
                result = split_audiobook(source_file)

                if args.disk or args.track:
                    output_dir = _get_output_dir(source_file)
                    output_dirs.add(output_dir)

        except (OSError, RuntimeError, ValueError) as exc:
            failed_count += 1
            print(
                f"ERROR: {source_file.name}: {exc}",
                file=sys.stderr,
            )
            continue

        if result is SplitResult.SPLIT:
            split_count += 1
            message = "Would split" if args.dry_run else "Split successfully"
            print(f"{message}: {source_file.name}")

        elif result is SplitResult.SKIPPED:
            skipped_count += 1
            print(f"Skipped (no suitable cut points): {source_file.name}")

        else:
            failed_count += 1
            print(
                f"ERROR: Unexpected result for {source_file.name}: {result!r}",
                file=sys.stderr,
            )

    if args.disk or args.track:
        for output_dir in sorted(
            output_dirs,
            key=lambda path: str(path).casefold(),
        ):
            if args.dry_run:
                print(f"\nPlanned metadata assignment: {output_dir.name}")

                if args.disk:
                    print("  Disc numbers (TPOS): would be assigned first.")

                if args.track:
                    print("  Track numbers (TRCK): would be assigned second.")

                continue

            try:
                if not output_dir.is_dir():
                    raise FileNotFoundError(
                        f"Output directory does not exist: {output_dir}"
                    )

                output_paths = _get_mp3_files(output_dir)

                if args.disk:
                    assign_disc_tags(output_paths)
                    print(f"Assigned disc numbers: {output_dir.name}")

                if args.track:
                    assign_track_tags(output_paths)
                    print(f"Assigned track numbers: {output_dir.name}")

            except (OSError, RuntimeError, ValueError) as exc:
                failed_count += 1
                print(
                    f"ERROR: Metadata assignment for {output_dir.name}: {exc}",
                    file=sys.stderr,
                )

    _print_summary(
        split_count,
        skipped_count,
        failed_count,
        len(mp3_files),
        dry_run=args.dry_run,
    )

    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
