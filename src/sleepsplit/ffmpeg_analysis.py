"""Run FFmpeg to detect silent intervals in audio files."""

import math
import re
import subprocess
from pathlib import Path

from sleepsplit.silence_detection import parse_silence_output


class SilenceDetectionError(RuntimeError):
    """Raised when FFmpeg cannot analyze an audio file."""


NOISE_THRESHOLD_PATTERN = re.compile(
    r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:dB)?",
    re.IGNORECASE,
)


def detect_silence(
    audio_file: str | Path,
    *,
    noise_threshold: str = "-40dB",
    minimum_silence_duration: float = 0.5,
) -> list[tuple[float, float]]:
    """Detect silent intervals in an audio file using FFmpeg.

    Args:
        audio_file: Path to the audio file to analyze.
        noise_threshold: Silence detection threshold, e.g. "-40dB" or "0.01".
        minimum_silence_duration: Minimum silence duration in seconds.

    Returns:
        A list of (start, end) tuples representing silent intervals.

    Raises:
        ValueError: If a configuration parameter is invalid.
        SilenceDetectionError: If FFmpeg is missing or analysis fails.
    """
    if not math.isfinite(minimum_silence_duration) or minimum_silence_duration <= 0:
        raise ValueError(
            "minimum_silence_duration must be finite and greater than zero."
        )

    threshold = noise_threshold.strip()

    if not threshold or NOISE_THRESHOLD_PATTERN.fullmatch(threshold) is None:
        raise ValueError(
            "noise_threshold must be a numeric value, optionally followed by dB."
        )

    if threshold.lower().endswith("db"):
        numeric_part = threshold[:-2]
        if float(numeric_part) > 0:
            raise ValueError("noise_threshold with dB must be zero or negative.")

    command = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(audio_file),
        "-af",
        f"silencedetect=noise={threshold}:d={minimum_silence_duration}",
        "-f",
        "null",
        "-",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise SilenceDetectionError(
            "FFmpeg was not found. Install FFmpeg or check your PATH."
        ) from error
    except subprocess.CalledProcessError as error:
        details = (error.stderr or "").strip()
        message = "FFmpeg could not analyze the audio file."
        if details:
            message += f" Details: {details}"
        raise SilenceDetectionError(message) from error

    return parse_silence_output(result.stderr)
