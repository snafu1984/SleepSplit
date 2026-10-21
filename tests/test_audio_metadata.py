"""Tests for reading audio metadata."""

import subprocess
from pathlib import Path

import pytest

from sleepsplit.audio_metadata import (
    AudioMetadataError,
    get_album_name,
    get_audio_duration,
)


def test_returns_audio_duration(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_run(command, **kwargs):
        assert command[0] == "ffprobe"
        assert str(tmp_path / "audiobook.mp3") in command
        assert kwargs == {
            "capture_output": True,
            "text": True,
            "check": True,
        }
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="722.000000\n",
            stderr="",
        )

    monkeypatch.setattr(
        "sleepsplit.audio_metadata.subprocess.run",
        fake_run,
    )

    assert get_audio_duration(tmp_path / "audiobook.mp3") == 722.0


def test_raises_error_when_ffprobe_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(
        "sleepsplit.audio_metadata.subprocess.run",
        fake_run,
    )

    with pytest.raises(AudioMetadataError, match="FFprobe was not found"):
        get_audio_duration(tmp_path / "audiobook.mp3")


def test_raises_error_when_ffprobe_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["ffprobe"],
            stderr="Invalid input",
        )

    monkeypatch.setattr(
        "sleepsplit.audio_metadata.subprocess.run",
        fake_run,
    )

    with pytest.raises(AudioMetadataError, match="Invalid input"):
        get_audio_duration(tmp_path / "audiobook.mp3")


def test_raises_error_for_invalid_duration(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="N/A\n",
            stderr="",
        )

    monkeypatch.setattr(
        "sleepsplit.audio_metadata.subprocess.run",
        fake_run,
    )

    with pytest.raises(AudioMetadataError, match="invalid audio duration"):
        get_audio_duration(tmp_path / "audiobook.mp3")


def test_returns_album_name(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_run(command, **kwargs):
        assert "format_tags=album" in command
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="Mein Hörbuch\n",
            stderr="",
        )

    monkeypatch.setattr(
        "sleepsplit.audio_metadata.subprocess.run",
        fake_run,
    )

    assert get_album_name(tmp_path / "kapitel.mp3") == "Mein Hörbuch"


def test_strips_whitespace_from_album_name(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="  Mein Hörbuch  \n",
            stderr="",
        )

    monkeypatch.setattr(
        "sleepsplit.audio_metadata.subprocess.run",
        fake_run,
    )

    assert get_album_name(tmp_path / "kapitel.mp3") == "Mein Hörbuch"


def test_returns_empty_string_when_album_tag_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        "sleepsplit.audio_metadata.subprocess.run",
        fake_run,
    )

    assert get_album_name(tmp_path / "kapitel.mp3") == ""


def test_returns_empty_string_when_album_tag_is_only_whitespace(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="   \n",
            stderr="",
        )

    monkeypatch.setattr(
        "sleepsplit.audio_metadata.subprocess.run",
        fake_run,
    )

    assert get_album_name(tmp_path / "kapitel.mp3") == ""
