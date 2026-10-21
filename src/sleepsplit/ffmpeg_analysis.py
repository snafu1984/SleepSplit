"""Run FFmpeg to detect silent intervals in audio files."""

import subprocess
from pathlib import Path

from sleepsplit.silence_detection import parse_silence_output


class SilenceDetectionError(RuntimeError):
    """Raised when FFmpeg cannot analyze an audio file."""


def detect_silence(
    audio_file: str | Path,
    *,
    noise_threshold: str = "-40dB",
    minimum_silence_duration: float = 0.5,
) -> list[tuple[float, float]]:
    """Detect silent intervals in an audio file using FFmpeg.

    Args:
        audio_file: Path to the audio file to analyze.
        noise_threshold: Maximum noise level considered silence.
        minimum_silence_duration: Minimum silence duration in seconds.

    Returns:
        Detected silence intervals as (start, end) pairs in seconds.

    Raises:
        SilenceDetectionError: If FFmpeg is unavailable or analysis fails.
    """
    command = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(audio_file),
        "-af",
        (f"silencedetect=noise={noise_threshold}:d={minimum_silence_duration}"),
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
