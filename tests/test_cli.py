"""Tests for the SleepSplit command-line interface."""

from pathlib import Path

import pytest

from sleepsplit import cli
from sleepsplit.models import SplitResult


def test_processes_only_mp3_files_in_specified_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Process top-level MP3 files only, in case-insensitive order."""
    (tmp_path / "BookB.mp3").touch()
    (tmp_path / "BookA.MP3").touch()
    (tmp_path / "notes.txt").touch()

    subdirectory = tmp_path / "subdirectory"
    subdirectory.mkdir()
    (subdirectory / "Nested.mp3").touch()

    processed: list[str] = []

    def fake_split_audiobook(source_file: str | Path) -> SplitResult:
        processed.append(Path(source_file).name)
        return SplitResult.SPLIT

    monkeypatch.setattr(cli, "split_audiobook", fake_split_audiobook)
    monkeypatch.setattr(
        "sys.argv",
        ["sleepsplit", str(tmp_path)],
    )

    assert cli.main() == 0
    assert processed == ["BookA.MP3", "BookB.mp3"]


def test_empty_directory_returns_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["sleepsplit", str(tmp_path)],
    )

    assert cli.main() == 0
    assert "No MP3 files found" in capsys.readouterr().out


def test_continues_after_one_file_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "01.mp3").touch()
    (tmp_path / "02.mp3").touch()

    processed: list[str] = []

    def fake_split_audiobook(source_file: str | Path) -> SplitResult:
        name = Path(source_file).name
        processed.append(name)

        if name == "01.mp3":
            raise RuntimeError("simulated failure")

        return SplitResult.SPLIT

    monkeypatch.setattr(cli, "split_audiobook", fake_split_audiobook)
    monkeypatch.setattr(
        "sys.argv",
        ["sleepsplit", str(tmp_path)],
    )

    assert cli.main() == 1
    assert processed == ["01.mp3", "02.mp3"]

    output = capsys.readouterr()
    assert "Failed: 1" in output.out
    assert "Split successfully: 1" in output.out
    assert "simulated failure" in output.err


def test_skipped_file_is_counted_separately(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "short.mp3").touch()

    monkeypatch.setattr(
        cli,
        "split_audiobook",
        lambda source_file: SplitResult.SKIPPED,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["sleepsplit", str(tmp_path)],
    )

    assert cli.main() == 0

    output = capsys.readouterr().out
    assert "Skipped: 1" in output
    assert "Split successfully: 0" in output
    assert "Failed: 0" in output


def test_rejects_nonexistent_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "does-not-exist"
    monkeypatch.setattr(
        "sys.argv",
        ["sleepsplit", str(missing)],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_rejects_file_as_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "book.mp3"
    file_path.touch()

    monkeypatch.setattr(
        "sys.argv",
        ["sleepsplit", str(file_path)],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
