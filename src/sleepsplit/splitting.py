"""Split MP3 files using mp3splt."""

import math
import subprocess
from itertools import pairwise
from pathlib import Path

from sleepsplit.time_format import seconds_to_mp3splt_time


def split_audio(
    source_file: str | Path,
    cut_points: list[float],
    output_paths: list[Path],
) -> None:
    """Split an MP3 file at the given absolute cut points.

    Raises:
        FileExistsError: If a planned output file already exists.
        RuntimeError: If mp3splt is unavailable or splitting fails.
        ValueError: If the output paths and cut points are inconsistent.
    """
    source_path = Path(source_file)
    outputs = [Path(path) for path in output_paths]

    if any(not math.isfinite(point) for point in cut_points):
        raise ValueError("Cut points must be finite.")

    if any(point < 0 for point in cut_points):
        raise ValueError("Cut points must be non-negative.")

    if any(current >= following for current, following in pairwise(cut_points)):
        raise ValueError("Cut points must be in strictly ascending order.")

    if len(outputs) != len(cut_points) + 1:
        raise ValueError(
            "The number of output paths must equal the number of cut points plus one."
        )

    if any(path.exists() for path in outputs):
        raise FileExistsError("An output file already exists.")

    if not outputs:
        raise ValueError("At least one output path is required.")

    expected_names = [
        f"{source_path.stem}_{number:03d}.mp3" for number in range(1, len(outputs) + 1)
    ]

    if [path.name for path in outputs] != expected_names:
        raise ValueError(
            "Output filenames must match the source filename and numbering."
        )

    output_dir = outputs[0].parent

    if any(path.parent != output_dir for path in outputs):
        raise ValueError("All output files must use the same directory.")

    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "mp3splt",
        "-q",
        "-d",
        str(output_dir),
        "-o",
        "@f_@n3",
        str(source_path),
        "0.00",
        *(seconds_to_mp3splt_time(point) for point in cut_points),
        "EOF",
    ]

    try:
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("mp3splt was not found. Check your PATH.") from error
    except subprocess.CalledProcessError as error:
        details = (error.stderr or "").strip()
        message = "mp3splt could not split the audio file."
        if details:
            message += f" Details: {details}"
        raise RuntimeError(message) from error

    missing_outputs = [path for path in outputs if not path.is_file()]

    if missing_outputs:
        missing_names = ", ".join(path.name for path in missing_outputs)
        raise RuntimeError(
            "mp3splt did not create all expected output files. "
            f"Missing: {missing_names}"
        )
