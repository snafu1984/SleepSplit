from sleepsplit.silence_detection import parse_silence_output


def test_parses_one_silence_interval() -> None:
    output = """
    [silencedetect] silence_start: 2.999977
    [silencedetect] silence_end: 5.000023 | silence_duration: 2.000045
    """

    assert parse_silence_output(output) == [(2.999977, 5.000023)]


def test_parses_multiple_silence_intervals() -> None:
    output = """
    silence_start: 2.0
    silence_end: 4.0 | silence_duration: 2.0
    silence_start: 10.5
    silence_end: 12.5 | silence_duration: 2.0
    """

    assert parse_silence_output(output) == [
        (2.0, 4.0),
        (10.5, 12.5),
    ]


def test_ignores_unrelated_output() -> None:
    output = """
    Input #0, mp3, from 'audio.mp3':
    Duration: 00:10:00.00
    Stream #0:0: Audio: mp3
    """

    assert parse_silence_output(output) == []


def test_ignores_incomplete_silence_interval() -> None:
    output = """
    silence_start: 25.0
    """

    assert parse_silence_output(output) == []


def test_ignores_end_before_start() -> None:
    output = """
    silence_start: 5.0
    silence_end: 3.0 | silence_duration: -2.0
    """

    assert parse_silence_output(output) == []


def test_ignores_negative_start_time() -> None:
    output = """
    silence_start: -2.0
    silence_end: 3.0 | silence_duration: 5.0
    """

    assert parse_silence_output(output) == []


def test_uses_latest_start_when_another_start_appears_before_end() -> None:
    output = """
    silence_start: 2.0
    silence_start: 5.0
    silence_end: 8.0 | silence_duration: 3.0
    """

    assert parse_silence_output(output) == [(5.0, 8.0)]


def test_ignores_overflowing_timestamps() -> None:
    output = """
    silence_start: 1e999
    silence_end: 1e1000 | silence_duration: 1e1000
    """

    assert parse_silence_output(output) == []
