"""Tests for disc assignment and ID3 TPOS tags."""

from pathlib import Path

import pytest
from mutagen.id3 import ID3, TIT2

from sleepsplit.disk_assignment import _plan_disc_groups, assign_disc_tags


def test_groups_segments_into_discs_near_sixty_minutes() -> None:
    durations = [300.0] * 24

    disc_numbers = _plan_disc_groups(durations)

    assert disc_numbers[:12] == [1] * 12
    assert disc_numbers[12:] == [2] * 12


def test_allows_a_short_final_disc() -> None:
    """Keep a full 60-minute disc and allow a shorter final disc."""
    durations = [300.0] * 15

    disc_numbers = _plan_disc_groups(durations)

    assert disc_numbers == [1] * 12 + [2] * 3


def test_rejects_segment_longer_than_sixty_five_minutes() -> None:
    with pytest.raises(ValueError, match="exceeds 65 minutes"):
        _plan_disc_groups([4000.0])


def test_rejects_unassignable_segments() -> None:
    with pytest.raises(ValueError, match="Cannot assign segments"):
        _plan_disc_groups([2000.0, 2000.0])


def test_writes_two_digit_disc_tags_and_preserves_title(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = [tmp_path / "segment_001.mp3", tmp_path / "segment_002.mp3"]

    # Mock MP3 duration lookup so this test does not require valid audio data.
    class FakeInfo:
        length = 3600.0

    class FakeMP3:
        def __init__(self, path: Path) -> None:
            self.info = FakeInfo()

    monkeypatch.setattr("sleepsplit.disk_assignment.MP3", FakeMP3)

    for path in paths:
        tags = ID3()
        tags.add(TIT2(encoding=3, text=["Test title"]))
        tags.save(path)

    assign_disc_tags(paths)

    first_tags = ID3(paths[0])
    second_tags = ID3(paths[1])

    assert str(first_tags["TPOS"]) == "01/02"
    assert str(second_tags["TPOS"]) == "02/02"
    assert str(first_tags["TIT2"]) == "Test title"
    assert str(second_tags["TIT2"]) == "Test title"
