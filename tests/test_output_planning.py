from pathlib import Path

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
