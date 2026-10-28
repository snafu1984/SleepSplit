from sleepsplit.cut_point_selection import select_absolute_cut_point


def test_returns_absolute_cut_point() -> None:
    pauses = [(590.0, 594.0)]

    assert select_absolute_cut_point(pauses, segment_start=300.0) == 592.0


def test_selects_pause_closest_to_target() -> None:
    pauses = [
        (540.0, 544.0),  # Mittelpunkt 542, relativ 242 Sekunden
        (590.0, 594.0),  # Mittelpunkt 592, relativ 292 Sekunden
        (650.0, 654.0),  # Mittelpunkt 652, relativ 352 Sekunden
    ]

    assert select_absolute_cut_point(pauses, segment_start=300.0) == 592.0


def test_ignores_pauses_outside_allowed_range() -> None:
    pauses = [
        (500.0, 510.0),  # Mittelpunkt relativ 205 Sekunden
        (730.0, 740.0),  # Mittelpunkt relativ 435 Sekunden
    ]

    assert select_absolute_cut_point(pauses, segment_start=300.0) is None


def test_returns_none_for_empty_pauses() -> None:
    assert select_absolute_cut_point([], segment_start=0.0) is None


def test_accepts_pause_at_minimum_duration_boundary() -> None:
    pauses = [(539.0, 541.0)]  # Mittelpunkt 540, relativ 240 Sekunden

    assert select_absolute_cut_point(pauses, segment_start=300.0) == 540.0


def test_accepts_pause_at_maximum_duration_boundary() -> None:
    pauses = [(719.0, 721.0)]  # Mittelpunkt 720, relativ 420 Sekunden

    assert select_absolute_cut_point(pauses, segment_start=300.0) == 720.0


def test_selects_earlier_pause_when_equally_close() -> None:
    pauses = [
        (538.0, 542.0),  # Mittelpunkt 540, relativ 240 Sekunden
        (658.0, 662.0),  # Mittelpunkt 660, relativ 360 Sekunden
    ]

    assert select_absolute_cut_point(pauses, segment_start=300.0) == 540.0
