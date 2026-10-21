from pathlib import Path

from sleepsplit.analysis import (
    find_cut_points,
    find_next_cut_point,
    plan_cut_points,
)


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


def test_finds_multiple_cut_points_from_one_analysis(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls = 0

    def fake_detect_silence(
        audio_file: str | Path,
    ) -> list[tuple[float, float]]:
        nonlocal calls
        calls += 1
        return [
            (290.0, 294.0),
            (394.0, 398.0),
            (598.0, 602.0),
        ]

    monkeypatch.setattr(
        "sleepsplit.analysis.detect_silence",
        fake_detect_silence,
    )

    cut_points = find_cut_points(tmp_path / "audiobook.mp3")

    assert cut_points == [292.0, 600.0]
    assert calls == 1


def test_returns_empty_list_when_no_suitable_pause_exists(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def fake_detect_silence(
        audio_file: str | Path,
    ) -> list[tuple[float, float]]:
        return [(10.0, 20.0), (100.0, 110.0)]

    monkeypatch.setattr(
        "sleepsplit.analysis.detect_silence",
        fake_detect_silence,
    )

    assert find_cut_points(tmp_path / "audiobook.mp3") == []


def test_plans_cuts_without_creating_a_short_final_segment() -> None:
    pauses = [
        (290.0, 294.0),
        (394.0, 398.0),
        (598.0, 602.0),
    ]

    cut_points = plan_cut_points(pauses, audio_duration=722.0)

    assert cut_points == [396.0]


def test_keeps_a_normal_final_segment() -> None:
    pauses = [
        (290.0, 294.0),
        (598.0, 602.0),
    ]

    cut_points = plan_cut_points(pauses, audio_duration=900.0)

    assert cut_points == [292.0, 600.0]


def test_returns_no_cuts_when_audio_fits_in_one_segment() -> None:
    pauses = [(290.0, 294.0)]

    cut_points = plan_cut_points(pauses, audio_duration=350.0)

    assert cut_points == []


def test_fallback_avoids_an_overlong_intermediate_segment() -> None:
    pauses = [
        (290.0, 294.0),
        (890.0, 894.0),
    ]

    cut_points = plan_cut_points(pauses, audio_duration=1000.0)

    assert cut_points == [292.0]


def test_uses_available_pause_when_no_fully_valid_plan_exists() -> None:
    pauses = [(290.0, 294.0)]

    cut_points = plan_cut_points(pauses, audio_duration=600.0)

    assert cut_points == [292.0]


def test_allows_short_final_segment_after_valid_segments() -> None:
    pauses = [
        (290.0, 294.0),
        (690.0, 694.0),
    ]

    cut_points = plan_cut_points(pauses, audio_duration=800.0)

    assert cut_points == [292.0, 692.0]


def test_fallback_does_not_create_an_overlong_middle_segment() -> None:
    pauses = [
        (290.0, 294.0),
        (890.0, 894.0),
    ]

    cut_points = plan_cut_points(pauses, audio_duration=1000.0)

    assert cut_points == [292.0]


def test_fallback_keeps_valid_segments_before_short_final_segment() -> None:
    pauses = [
        (290.0, 294.0),
        (394.0, 398.0),
        (598.0, 602.0),
    ]

    cut_points = plan_cut_points(pauses, audio_duration=722.0)

    assert cut_points == [396.0]
