import subprocess
from pathlib import Path

import pytest

from sleepsplit.ffmpeg_analysis import (
    SilenceDetectionError,
    detect_silence,
)


def test_detects_silence_from_ffmpeg_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "my audiobook.mp3"
    output = """
    silence_start: 3.0
    silence_end: 5.0 | silence_duration: 2.0
    """

    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr=output,
        )

    monkeypatch.setattr("sleepsplit.ffmpeg_analysis.subprocess.run", fake_run)

    assert detect_silence(audio_file) == [(3.0, 5.0)]


def test_calls_ffmpeg_with_silencedetect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    audio_file = tmp_path / "audiobook.mp3"
    captured: dict[str, object] = {}

    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr("sleepsplit.ffmpeg_analysis.subprocess.run", fake_run)

    detect_silence(audio_file)

    command = captured["command"]
    kwargs = captured["kwargs"]

    assert isinstance(command, list)
    assert command[0] == "ffmpeg"
    assert str(audio_file) in command
    assert any(argument.startswith("silencedetect=") for argument in command)
    assert isinstance(kwargs, dict)
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["check"] is True


def test_reports_ffmpeg_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=command,
            stderr="Invalid input file",
        )

    monkeypatch.setattr("sleepsplit.ffmpeg_analysis.subprocess.run", fake_run)

    with pytest.raises(SilenceDetectionError, match="Invalid input file"):
        detect_silence(tmp_path / "broken.mp3")


def test_reports_missing_ffmpeg(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("ffmpeg not found")

    monkeypatch.setattr("sleepsplit.ffmpeg_analysis.subprocess.run", fake_run)

    with pytest.raises(SilenceDetectionError, match="FFmpeg"):
        detect_silence(tmp_path / "audiobook.mp3")
