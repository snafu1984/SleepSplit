"""Tests for the audiobook splitting pipeline."""

from pathlib import Path

import pytest

from sleepsplit import pipeline


def test_does_nothing_when_no_cut_points_are_found(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_file = tmp_path / "audiobook.mp3"
    source_file.touch()

    monkeypatch.setattr(
        "sleepsplit.pipeline.get_audio_duration",
        lambda audio_file: 200.0,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.get_album_name",
        lambda audio_file: "Test_Album_cut",
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.detect_silence",
        lambda audio_file: [],
    )

    def unexpected_call(*args, **kwargs):
        raise AssertionError("No output planning or splitting should occur.")

    monkeypatch.setattr(
        "sleepsplit.pipeline.plan_output_paths",
        unexpected_call,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.split_audio",
        unexpected_call,
    )

    pipeline.split_audiobook(source_file)

    assert list(tmp_path.iterdir()) == [source_file]


def test_splits_audiobook_using_planned_cut_points(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_file = tmp_path / "audiobook.mp3"
    source_file.touch()

    calls = {}

    monkeypatch.setattr(
        "sleepsplit.pipeline.get_audio_duration",
        lambda audio_file: 900.0,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.get_album_name",
        lambda audio_file: "Test_Album",
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.detect_silence",
        lambda audio_file: [(290.0, 294.0), (590.0, 594.0)],
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.split_audio",
        lambda source, cuts, outputs: calls.update(
            source=source,
            cuts=cuts,
            outputs=outputs,
        ),
    )

    pipeline.split_audiobook(source_file)

    assert calls["source"] == source_file
    assert calls["cuts"] == [292.0, 592.0]
    assert calls["outputs"] == [
        tmp_path / "Test_Album_cut" / "audiobook_001.mp3",
        tmp_path / "Test_Album_cut" / "audiobook_002.mp3",
        tmp_path / "Test_Album_cut" / "audiobook_003.mp3",
    ]
    assert not (tmp_path / "Test_Album_cut").exists()


def test_does_not_split_when_output_file_already_exists(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_file = tmp_path / "audiobook.mp3"
    source_file.touch()

    output_dir = tmp_path / "Test_Album_cut"
    output_dir.mkdir()
    existing_output = output_dir / "audiobook_001.mp3"
    existing_output.touch()

    monkeypatch.setattr(
        "sleepsplit.pipeline.get_audio_duration",
        lambda audio_file: 900.0,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.get_album_name",
        lambda audio_file: "Test_Album",
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.detect_silence",
        lambda audio_file: [(290.0, 294.0), (590.0, 594.0)],
    )

    def unexpected_split(*args, **kwargs):
        raise AssertionError("The splitter must not be called.")

    monkeypatch.setattr(
        "sleepsplit.pipeline.split_audio",
        unexpected_split,
    )

    with pytest.raises(FileExistsError):
        pipeline.split_audiobook(source_file)

    assert existing_output.is_file()


@pytest.mark.parametrize(
    "duration",
    [float("nan"), float("inf"), float("-inf")],
)
def test_rejects_non_finite_audio_duration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    duration: float,
) -> None:
    source_file = tmp_path / "audiobook.mp3"
    source_file.touch()

    monkeypatch.setattr(
        "sleepsplit.pipeline.get_audio_duration",
        lambda audio_file: duration,
    )

    def unexpected_call(*args, **kwargs):
        pytest.fail("Processing must stop for a non-finite duration.")

    monkeypatch.setattr(
        "sleepsplit.pipeline.detect_silence",
        unexpected_call,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.plan_output_paths",
        unexpected_call,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.split_audio",
        unexpected_call,
    )

    with pytest.raises(ValueError, match="duration"):
        pipeline.split_audiobook(source_file)
