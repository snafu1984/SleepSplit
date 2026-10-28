"""Tests for the SleepSplit command-line interface."""

from pathlib import Path

import pytest

from sleepsplit import cli
from sleepsplit.models import SplitResult


def assert_summary_count(
    output: str,
    label: str,
    expected: int,
) -> None:
    """Assert the count displayed for one summary category."""
    matching_lines = [
        line
        for line in output.splitlines()
        if line.strip().startswith(label) and line.split(":")[-1].strip().isdigit()
    ]

    assert len(matching_lines) == 1
    assert int(matching_lines[0].split(":")[-1].strip()) == expected


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
    assert_summary_count(output.out, "Failed:", 1)
    assert_summary_count(output.out, "Split successfully:", 1)
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
    assert_summary_count(output, "Skipped:", 1)
    assert_summary_count(output, "Split successfully:", 0)
    assert_summary_count(output, "Failed:", 0)


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


def test_dry_run_displays_planned_outputs_without_splitting(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Display the plan without invoking the actual splitting pipeline."""
    from sleepsplit.models import AudiobookPlan

    source_file = tmp_path / "Book.mp3"
    source_file.touch()

    output_paths = [
        tmp_path / "Book_cut" / "Book_001.mp3",
        tmp_path / "Book_cut" / "Book_002.mp3",
    ]

    monkeypatch.setattr(
        cli,
        "plan_audiobook",
        lambda source: AudiobookPlan(
            cut_points=[300.0],
            output_paths=output_paths,
        ),
    )

    def unexpected_split(*args, **kwargs):
        pytest.fail("Dry-run must not call split_audiobook.")

    monkeypatch.setattr(cli, "split_audiobook", unexpected_split)
    monkeypatch.setattr(
        "sys.argv",
        ["sleepsplit", "--dry-run", str(tmp_path)],
    )

    assert cli.main() == 0

    output = capsys.readouterr().out
    assert "DRY RUN" in output
    assert "Cut 1: 300.00 seconds" in output
    assert str(output_paths[0]) in output
    assert str(output_paths[1]) in output
    assert_summary_count(output, "Would split:", 1)
    assert_summary_count(output, "Failed:", 0)

    assert not (tmp_path / "Book_cut").exists()
    assert source_file.is_file()


def test_dry_run_counts_unplannable_file_as_skipped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Count files without a valid plan as skipped during dry-run."""
    (tmp_path / "Short.mp3").touch()

    monkeypatch.setattr(cli, "plan_audiobook", lambda source: None)
    monkeypatch.setattr(
        "sys.argv",
        ["sleepsplit", "--dry-run", str(tmp_path)],
    )

    assert cli.main() == 0

    output = capsys.readouterr().out
    assert_summary_count(output, "Skipped:", 1)
    assert_summary_count(output, "Would split:", 0)
    assert_summary_count(output, "Failed:", 0)
