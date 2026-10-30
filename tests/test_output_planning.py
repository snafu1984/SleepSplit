"""Tests for planning output paths for split audio segments."""

import subprocess
from pathlib import Path

import pytest

from sleepsplit.audio_metadata import get_album_name
from sleepsplit.output_planning import plan_output_paths


def test_creates_numbered_paths_in_album_directory() -> None:
    source = Path("/audiobooks/Kapitel_01.mp3")

    output_paths = plan_output_paths(
        source_file=source,
        album_name="Mein Album",
        segment_count=3,
    )

    assert output_paths == [
        Path("/audiobooks/Mein_Album_cut/Kapitel_01_001.mp3"),
        Path("/audiobooks/Mein_Album_cut/Kapitel_01_002.mp3"),
        Path("/audiobooks/Mein_Album_cut/Kapitel_01_003.mp3"),
    ]


def test_starts_numbering_at_one_for_each_source_file() -> None:
    source = Path("/audiobooks/Kapitel_02.mp3")

    output_paths = plan_output_paths(
        source_file=source,
        album_name="Mein Album",
        segment_count=2,
    )

    assert output_paths == [
        Path("/audiobooks/Mein_Album_cut/Kapitel_02_001.mp3"),
        Path("/audiobooks/Mein_Album_cut/Kapitel_02_002.mp3"),
    ]


def test_supports_a_source_filename_without_spaces_or_extra_suffixes() -> None:
    source = Path("/audiobooks/Track.mp3")

    output_paths = plan_output_paths(
        source_file=source,
        album_name="Hörbuch",
        segment_count=1,
    )

    assert output_paths == [
        Path("/audiobooks/Hoerbuch_cut/Track_001.mp3"),
    ]


def test_album_name_can_be_used_to_plan_output_paths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "Kapitel_01.mp3"

    def fake_run(command, **kwargs):
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

    album_name = get_album_name(source)
    output_paths = plan_output_paths(
        source_file=source,
        album_name=album_name,
        segment_count=2,
    )

    assert output_paths == [
        tmp_path / "Mein_Hoerbuch_cut" / "Kapitel_01_001.mp3",
        tmp_path / "Mein_Hoerbuch_cut" / "Kapitel_01_002.mp3",
    ]
    assert not (tmp_path / "Mein_Hoerbuch_cut").exists()


def test_rejects_zero_segments() -> None:
    with pytest.raises(ValueError, match="segment_count must be at least 1"):
        plan_output_paths(
            source_file=Path("/audiobooks/Kapitel_01.mp3"),
            album_name="Mein Album",
            segment_count=0,
        )


def test_rejects_source_file_without_mp3_extension() -> None:
    with pytest.raises(ValueError, match="source_file must be an MP3 file"):
        plan_output_paths(
            source_file=Path("/audiobooks/Kapitel_01.wav"),
            album_name="Mein Album",
            segment_count=2,
        )


def test_rejects_album_name_with_directory_separator() -> None:
    with pytest.raises(
        ValueError,
        match="album_name must be a single directory name",
    ):
        plan_output_paths(
            source_file=Path("/audiobooks/Kapitel_01.mp3"),
            album_name="../Anderes Album",
            segment_count=2,
        )


def test_places_output_files_in_cut_directory_when_album_is_empty() -> None:
    source = Path("/audiobooks/Kapitel_01.mp3")

    output_paths = plan_output_paths(
        source_file=source,
        album_name="",
        segment_count=2,
    )

    assert output_paths == [
        Path("/audiobooks/cut/Kapitel_01_001.mp3"),
        Path("/audiobooks/cut/Kapitel_01_002.mp3"),
    ]
