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

    assert cut_points == [292.0]


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

    assert cut_points == []


def test_uses_available_pause_when_valid_plan_exists() -> None:
    pauses = [(290.0, 294.0)]

    cut_points = plan_cut_points(pauses, audio_duration=600.0)

    assert cut_points == [292.0]


def test_allows_short_final_segment_after_valid_segments() -> None:
    pauses = [(358.0, 362.0)]

    cut_points = plan_cut_points(pauses, audio_duration=480.0)

    assert cut_points == [360.0]


def test_prefers_target_duration_when_multiple_valid_plans_exist() -> None:
    pauses = [
        (290.0, 294.0),
        (394.0, 398.0),
        (598.0, 602.0),
    ]

    cut_points = plan_cut_points(pauses, audio_duration=722.0)

    assert cut_points == [292.0]


def test_does_not_claim_valid_plan_with_overlong_final_segment() -> None:
    pauses = [(290.0, 294.0)]

    cut_points = plan_cut_points(pauses, audio_duration=1000.0)

    assert cut_points == []


def test_does_not_split_audio_shorter_than_420_seconds() -> None:
    assert plan_cut_points([], audio_duration=419.0) == []


def test_does_not_split_audio_exactly_420_seconds() -> None:
    assert (
        plan_cut_points(
            [(300.0, 304.0)],
            audio_duration=420.0,
        )
        == []
    )


def test_allows_cut_planning_above_420_seconds() -> None:
    pauses = [(298.0, 302.0)]

    assert plan_cut_points(pauses, audio_duration=421.0) == [300.0]


def test_accepts_final_segment_of_exactly_120_seconds() -> None:
    pauses = [(358.0, 362.0)]

    assert plan_cut_points(pauses, audio_duration=480.0) == [360.0]


def test_accepts_final_segment_of_exactly_540_seconds() -> None:
    pauses = [(298.0, 302.0)]

    assert plan_cut_points(pauses, audio_duration=840.0) == [300.0]


def test_does_not_accept_final_segment_shorter_than_120_seconds() -> None:
    pauses = [(358.0, 362.0)]

    assert plan_cut_points(pauses, audio_duration=479.0) == []


def test_does_not_accept_final_segment_longer_than_540_seconds() -> None:
    pauses = [(298.0, 302.0)]

    assert plan_cut_points(pauses, audio_duration=841.0) == []


def test_does_not_allow_regular_segment_shorter_than_240_seconds() -> None:
    pauses = [
        (198.0, 202.0),
        (438.0, 442.0),
    ]

    cut_points = plan_cut_points(pauses, audio_duration=660.0)

    assert cut_points == []
