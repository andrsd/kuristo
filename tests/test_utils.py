import pytest
from unittest.mock import MagicMock
from kuristo.utils import interpolate_str, minutes_to_hhmmss, human_time
from kuristo.utils import build_filters


def test_interpolate_str_vars():
    str = interpolate_str("${{ first }} ${{ second }}", {"first": 1, "second": "two"})
    assert str == "1 two"


def test_interpolate_str_vars_and_none():
    str = interpolate_str("asdf ${{ matrix.op }}", {"matrix": None})
    assert str == "asdf "


def test_interpolate_str_none():
    str = interpolate_str("asdf", {"matrix": None})
    assert str == "asdf"


def test_interpolate_str_():
    with pytest.raises(TypeError):
        interpolate_str("asdf", None)


def test_minutes_to_hhmmss():
    assert minutes_to_hhmmss(0) == "0:00:00"
    assert minutes_to_hhmmss(1) == "0:01:00"
    assert minutes_to_hhmmss(12) == "0:12:00"
    assert minutes_to_hhmmss(60) == "1:00:00"
    assert minutes_to_hhmmss(69) == "1:09:00"
    assert minutes_to_hhmmss(180) == "3:00:00"


def test_human_time():
    assert human_time(1) == "1.00s"
    assert human_time(1.06) == "1.06s"
    assert human_time(61.2) == "1m 1.20s"
    assert human_time(3765.2) == "1h 2m 45.20s"


def test_build_filters():
    args = MagicMock()
    args.passed = True
    args.skipped = True
    args.failed = True
    assert build_filters(args) == ["failed", "skipped", "success"]
