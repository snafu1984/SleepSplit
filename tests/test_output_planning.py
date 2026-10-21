"""Tests for planning output paths for split audio segments."""

import subprocess
from pathlib import Path

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
        Path("/audiobooks/Mein Album/Kapitel_01_001.mp3"),
        Path("/audiobooks/Mein Album/Kapitel_01_002.mp3"),
        Path("/audiobooks/Mein Album/Kapitel_01_003.mp3"),
    ]


def test_starts_numbering_at_one_for_each_source_file() -> None:
    source = Path("/audiobooks/Kapitel_02.mp3")

    output_paths = plan_output_paths(
        source_file=source,
        album_name="Mein Album",
        segment_count=2,
    )

    assert output_paths == [
        Path("/audiobooks/Mein Album/Kapitel_02_001.mp3"),
        Path("/audiobooks/Mein Album/Kapitel_02_002.mp3"),
    ]


def test_supports_a_source_filename_without_spaces_or_extra_suffixes() -> None:
    source = Path("/audiobooks/Track.mp3")

    output_paths = plan_output_paths(
        source_file=source,
        album_name="Hörbuch",
        segment_count=1,
    )

    assert output_paths == [
        Path("/audiobooks/Hörbuch/Track_001.mp3"),
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
        tmp_path / "Mein Hörbuch" / "Kapitel_01_001.mp3",
        tmp_path / "Mein Hörbuch" / "Kapitel_01_002.mp3",
    ]
    assert not (tmp_path / "Mein Hörbuch").exists()
