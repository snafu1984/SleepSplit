"""Tests for the audiobook splitting pipeline."""

from pathlib import Path

import pytest

from sleepsplit import pipeline


def test_copies_audiobook_when_no_cut_points_are_found(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Copy an audiobook to the output directory when it cannot be split."""
    source_file = tmp_path / "audiobook.mp3"
    original_content = b"original audiobook data"
    source_file.write_bytes(original_content)

    monkeypatch.setattr(
        "sleepsplit.pipeline.get_audio_duration",
        lambda audio_file: 200.0,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.get_album_name",
        lambda audio_file: "Test_Album",
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.detect_silence",
        lambda audio_file: [],
    )

    result = pipeline.split_audiobook(source_file)

    output_file = tmp_path / "Test_Album_cut" / "audiobook.mp3"

    assert result is pipeline.SplitResult.SKIPPED
    assert output_file.read_bytes() == original_content
    assert source_file.read_bytes() == original_content
    assert source_file.is_file()


def test_does_not_overwrite_existing_unsplittable_output(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Preserve an existing output file when the audiobook cannot be split."""
    source_file = tmp_path / "audiobook.mp3"
    source_file.write_bytes(b"original content")

    output_dir = tmp_path / "Test_Album_cut"
    output_dir.mkdir()
    output_file = output_dir / "audiobook.mp3"
    output_file.write_bytes(b"existing content")

    monkeypatch.setattr(
        "sleepsplit.pipeline.get_audio_duration",
        lambda audio_file: 200.0,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.get_album_name",
        lambda audio_file: "Test_Album",
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.detect_silence",
        lambda audio_file: [],
    )

    with pytest.raises(FileExistsError):
        pipeline.split_audiobook(source_file)

    assert output_file.read_bytes() == b"existing content"


def test_dry_run_does_not_copy_unsplittable_audiobook(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Do not create output files during a dry-run with no suitable cuts."""
    source_file = tmp_path / "audiobook.mp3"
    original_content = b"original audiobook data"
    source_file.write_bytes(original_content)

    monkeypatch.setattr(
        "sleepsplit.pipeline.get_audio_duration",
        lambda audio_file: 200.0,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.get_album_name",
        lambda audio_file: "Test_Album",
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.detect_silence",
        lambda audio_file: [],
    )

    result = pipeline.split_audiobook(source_file, dry_run=True)

    assert result is pipeline.SplitResult.SKIPPED
    assert source_file.read_bytes() == original_content
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


def test_plan_audiobook_returns_cut_points_and_output_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Return the planned cuts and output paths without creating files."""
    source_file = tmp_path / "audiobook.mp3"
    source_file.touch()

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

    plan = pipeline.plan_audiobook(source_file)

    assert plan is not None
    assert plan.cut_points == [292.0, 592.0]
    assert plan.output_paths == [
        tmp_path / "Test_Album_cut" / "audiobook_001.mp3",
        tmp_path / "Test_Album_cut" / "audiobook_002.mp3",
        tmp_path / "Test_Album_cut" / "audiobook_003.mp3",
    ]
    assert list(tmp_path.iterdir()) == [source_file]


def test_dry_run_does_not_create_or_modify_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Dry-run plans a split without creating outputs or calling the splitter."""
    source_file = tmp_path / "audiobook.mp3"
    original_content = b"original audiobook data"
    source_file.write_bytes(original_content)

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
        pytest.fail("Dry-run must not call the splitter.")

    monkeypatch.setattr(
        "sleepsplit.pipeline.split_audio",
        unexpected_split,
    )

    result = pipeline.split_audiobook(source_file, dry_run=True)

    assert result is pipeline.SplitResult.SPLIT
    assert source_file.read_bytes() == original_content
    assert list(tmp_path.iterdir()) == [source_file]


def test_dry_run_skips_when_no_cut_points_are_found(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Skip a dry-run when no suitable cuts are available."""
    source_file = tmp_path / "audiobook.mp3"
    source_file.touch()

    monkeypatch.setattr(
        "sleepsplit.pipeline.get_audio_duration",
        lambda audio_file: 200.0,
    )
    monkeypatch.setattr(
        "sleepsplit.pipeline.detect_silence",
        lambda audio_file: [],
    )

    monkeypatch.setattr(
        "sleepsplit.pipeline.get_album_name",
        lambda audio_file: "Test_Album",
    )

    result = pipeline.split_audiobook(source_file, dry_run=True)

    assert result is pipeline.SplitResult.SKIPPED
    assert list(tmp_path.iterdir()) == [source_file]
