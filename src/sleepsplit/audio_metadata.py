"""Read audio file metadata using FFprobe."""

import subprocess
from pathlib import Path


class AudioMetadataError(RuntimeError):
    """Raised when audio metadata cannot be read."""


def get_audio_duration(audio_file: str | Path) -> float:
    """Return the duration of an audio file in seconds.

    Args:
        audio_file: Path to the audio file.

    Returns:
        Audio duration in seconds.

    Raises:
        AudioMetadataError: If FFprobe is unavailable or fails.
    """
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_file),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise AudioMetadataError(
            "FFprobe was not found. Install FFmpeg or check your PATH."
        ) from error
    except subprocess.CalledProcessError as error:
        details = (error.stderr or "").strip()
        message = "FFprobe could not read the audio metadata."
        if details:
            message += f" Details: {details}"
        raise AudioMetadataError(message) from error

    try:
        duration = float(result.stdout.strip())
    except ValueError as error:
        raise AudioMetadataError(
            "FFprobe returned an invalid audio duration."
        ) from error

    if duration < 0:
        raise AudioMetadataError("Audio duration must not be negative.")

    return duration
