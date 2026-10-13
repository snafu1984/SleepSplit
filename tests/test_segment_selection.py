from sleepsplit.segment_selection import select_cut_point


def test_selects_pause_closest_to_target() -> None:
    assert select_cut_point([275, 306, 338]) == 306


def test_returns_none_when_no_pause_is_in_allowed_range() -> None:
    assert select_cut_point([180, 230, 421, 450]) is None


def test_selects_earlier_pause_when_equally_close() -> None:
    assert select_cut_point([294, 306]) == 294


def test_returns_none_for_empty_list() -> None:
    assert select_cut_point([]) is None


def test_accepts_minimum_duration() -> None:
    assert select_cut_point([240]) == 240


def test_accepts_maximum_duration() -> None:
    assert select_cut_point([420]) == 420


def test_selects_pause_with_decimal_seconds() -> None:
    assert select_cut_point([275.5, 301.25, 338.75]) == 301.25
