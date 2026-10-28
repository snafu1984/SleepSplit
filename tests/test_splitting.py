"""Tests for splitting MP3 files with mp3splt."""

import subprocess
from pathlib import Path

import pytest

from sleepsplit.splitting import split_audio


def test_builds_mp3splt_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    output_dir.mkdir()
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
        output_dir / "book_003.mp3",
    ]
    calls: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        for output in outputs:
            output.touch()
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", fake_run)

    split_audio(
        source_file=source,
        cut_points=[300.0, 600.0],
        output_paths=outputs,
    )

    assert calls == [
        [
            "mp3splt",
            "-q",
            "-d",
            str(output_dir),
            "-o",
            "@f_@n3",
            str(source),
            "0.00",
            "5.00",
            "10.00",
            "EOF",
        ]
    ]


def test_creates_output_directory_before_splitting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Create the output directory before calling mp3splt."""
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
    ]
    calls: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert output_dir.is_dir()
        calls.append(command)
        for output in outputs:
            output.touch()
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", fake_run)

    split_audio(
        source_file=source,
        cut_points=[300.0],
        output_paths=outputs,
    )

    assert output_dir.is_dir()
    assert len(calls) == 1


def test_rejects_existing_output_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    output_dir.mkdir()
    existing_output = output_dir / "book_001.mp3"
    existing_output.touch()
    outputs = [
        existing_output,
        output_dir / "book_002.mp3",
    ]

    def unexpected_run(*args: object, **kwargs: object) -> None:
        pytest.fail("mp3splt must not run when an output file already exists")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", unexpected_run)

    with pytest.raises(FileExistsError, match="already exists"):
        split_audio(
            source_file=source,
            cut_points=[300.0],
            output_paths=outputs,
        )


def test_removes_partial_outputs_when_output_file_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remove partial output files when mp3splt omits an output file."""
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
    ]

    def incomplete_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        outputs[0].touch()
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", incomplete_run)

    with pytest.raises(
        RuntimeError,
        match="did not create all expected output files",
    ):
        split_audio(
            source_file=source,
            cut_points=[300.0],
            output_paths=outputs,
        )

    assert not any(path.exists() for path in outputs)


def test_raises_runtime_error_when_output_file_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise an error if mp3splt succeeds but omits an output file."""
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    output_dir.mkdir()
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
    ]

    def incomplete_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        outputs[0].touch()
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", incomplete_run)

    with pytest.raises(RuntimeError, match="did not create all expected output files"):
        split_audio(
            source_file=source,
            cut_points=[300.0],
            output_paths=outputs,
        )


def test_rejects_output_paths_with_wrong_filenames(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject output filenames that do not match the source filename."""
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    outputs = [
        output_dir / "other_001.mp3",
        output_dir / "other_002.mp3",
    ]

    def fail_if_called(*args: object, **kwargs: object) -> None:
        pytest.fail("mp3splt must not be called for invalid output paths")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", fail_if_called)

    with pytest.raises(ValueError, match="filenames"):
        split_audio(
            source_file=source,
            cut_points=[300.0],
            output_paths=outputs,
        )


def test_rejects_cut_points_that_are_not_in_ascending_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
        output_dir / "book_003.mp3",
    ]

    def unexpected_run(*args: object, **kwargs: object) -> None:
        pytest.fail("mp3splt must not run with unsorted cut points")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", unexpected_run)

    with pytest.raises(ValueError, match="ascending order"):
        split_audio(
            source_file=source,
            cut_points=[600.0, 300.0],
            output_paths=outputs,
        )


def test_rejects_negative_cut_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
    ]

    def unexpected_run(*args: object, **kwargs: object) -> None:
        pytest.fail("mp3splt must not run with negative cut points")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", unexpected_run)

    with pytest.raises(ValueError, match="non-negative"):
        split_audio(
            source_file=source,
            cut_points=[-1.0],
            output_paths=outputs,
        )


def test_rejects_duplicate_cut_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject duplicate cut points."""
    outputs = [
        tmp_path / "book_001.mp3",
        tmp_path / "book_002.mp3",
        tmp_path / "book_003.mp3",
    ]

    def fail_if_called(*args: object, **kwargs: object) -> None:
        pytest.fail("mp3splt must not be called for invalid cut points")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", fail_if_called)

    with pytest.raises(ValueError, match="strictly ascending"):
        split_audio(
            tmp_path / "book.mp3",
            cut_points=[300.0, 300.0],
            output_paths=outputs,
        )


@pytest.mark.parametrize("cut_point", [float("nan"), float("inf"), float("-inf")])
def test_rejects_non_finite_cut_points(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cut_point: float,
) -> None:
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
    ]

    def unexpected_run(*args: object, **kwargs: object) -> None:
        pytest.fail("mp3splt must not run with non-finite cut points")

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", unexpected_run)

    with pytest.raises(ValueError, match="finite"):
        split_audio(
            source_file=source,
            cut_points=[cut_point],
            output_paths=outputs,
        )


def test_raises_runtime_error_when_mp3splt_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise a helpful error when mp3splt is not available."""
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
    ]

    def missing_executable(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("mp3splt")

    monkeypatch.setattr(
        "sleepsplit.splitting.subprocess.run",
        missing_executable,
    )

    with pytest.raises(RuntimeError, match="mp3splt was not found"):
        split_audio(
            source_file=source,
            cut_points=[300.0],
            output_paths=outputs,
        )


def test_removes_partial_outputs_when_mp3splt_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remove partial output files when mp3splt fails."""
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
    ]

    def failed_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs[0].touch()
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=command,
            stderr="Test error from mp3splt",
        )

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", failed_run)

    with pytest.raises(RuntimeError, match="Test error from mp3splt"):
        split_audio(
            source_file=source,
            cut_points=[300.0],
            output_paths=outputs,
        )

    assert not any(path.exists() for path in outputs)


def test_preserves_original_error_when_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve the mp3splt error if cleanup also fails."""
    source = tmp_path / "book.mp3"
    output_dir = tmp_path / "Album"
    outputs = [
        output_dir / "book_001.mp3",
        output_dir / "book_002.mp3",
    ]

    def failed_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs[0].touch()
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=command,
            stderr="Original mp3splt error",
        )

    original_unlink = Path.unlink

    def failing_unlink(
        path: Path,
        *,
        missing_ok: bool = False,
    ) -> None:
        if path == outputs[0]:
            raise OSError("Simulated cleanup failure")
        original_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr("sleepsplit.splitting.subprocess.run", failed_run)
    monkeypatch.setattr(Path, "unlink", failing_unlink)

    with pytest.raises(RuntimeError, match="Original mp3splt error"):
        split_audio(
            source_file=source,
            cut_points=[300.0],
            output_paths=outputs,
        )

    assert outputs[0].exists()


def test_warns_when_partial_output_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Warn when a partial output cannot be removed."""
    from sleepsplit.splitting import _remove_partial_outputs

    output = tmp_path / "book_001.mp3"
    output.touch()

    def failing_unlink(
        path: Path,
        *,
        missing_ok: bool = False,
    ) -> None:
        raise OSError("Simulated cleanup failure")

    monkeypatch.setattr(Path, "unlink", failing_unlink)

    _remove_partial_outputs([output])

    captured = capsys.readouterr()
    assert "WARNING: Could not remove partial output" in captured.err
    assert str(output) in captured.err
    assert "Simulated cleanup failure" in captured.err
