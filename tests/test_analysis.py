from pathlib import Path

from sleepsplit.analysis import find_next_cut_point


def test_returns_absolute_cut_point(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_detect_silence(audio_file: str | Path) -> list[tuple[float, float]]:
        return [(590.0, 594.0)]

    monkeypatch.setattr(
        "sleepsplit.analysis.detect_silence",
        fake_detect_silence,
    )

    assert find_next_cut_point(tmp_path / "audiobook.mp3", 300.0) == 592.0


def test_returns_none_when_no_suitable_pause_exists(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_detect_silence(audio_file: str | Path) -> list[tuple[float, float]]:
        return [(400.0, 410.0)]

    monkeypatch.setattr(
        "sleepsplit.analysis.detect_silence",
        fake_detect_silence,
    )

    assert find_next_cut_point(tmp_path / "audiobook.mp3", 300.0) is None
