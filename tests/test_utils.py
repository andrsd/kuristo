import pytest
from kuristo.utils import interpolate_str


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
