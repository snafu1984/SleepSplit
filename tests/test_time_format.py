from sleepsplit.time_format import seconds_to_mp3splt_time


def test_formats_zero_seconds() -> None:
    assert seconds_to_mp3splt_time(0) == "0.00"


def test_formats_whole_seconds() -> None:
    assert seconds_to_mp3splt_time(4) == "0.04"


def test_formats_fractional_seconds() -> None:
    assert seconds_to_mp3splt_time(4.5) == "0.04.50"


def test_formats_minutes_and_seconds() -> None:
    assert seconds_to_mp3splt_time(65) == "1.05"


def test_formats_five_minutes() -> None:
    assert seconds_to_mp3splt_time(300) == "5.00"


def test_formats_more_than_one_hour() -> None:
    assert seconds_to_mp3splt_time(3661) == "61.01"


def test_rounds_to_hundredths() -> None:
    assert seconds_to_mp3splt_time(4.567) == "0.04.57"


def test_rounding_can_carry_into_next_minute() -> None:
    assert seconds_to_mp3splt_time(59.999) == "1.00"
