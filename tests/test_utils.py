from unittest.mock import MagicMock

import pytest

from kuristo.exceptions import UserException
from kuristo.utils import (
    build_filters,
    human_time,
    interpolate_str,
    interpolate_value,
    minutes_to_hhmmss,
    read_report,
)


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


def test_read_report_success(tmp_path):
    report_file = tmp_path / "report.yaml"
    report_file.write_text("""
total-runtime: 42.5
results:
  - id: 1
    status: success
""")
    data = read_report(report_file)
    assert data["total-runtime"] == 42.5
    assert data["results"][0]["id"] == 1


def test_read_report_not_found(tmp_path):
    missing_file = tmp_path / "does_not_exist.yaml"
    with pytest.raises(UserException) as excinfo:
        read_report(missing_file)
    assert "Report file not found" in str(excinfo.value)


def test_read_report_invalid_yaml(tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("""
invalid_yaml: [
""")
    with pytest.raises(UserException) as excinfo:
        read_report(bad_file)
    assert "Failed to parse report file" in str(excinfo.value)


def test_interpolate_value_success():
    vars = {"foo": "bar"}
    # String
    assert interpolate_value("${{ foo }}", vars) == "bar"
    # List
    assert interpolate_value(["${{ foo }}", "plain"], vars) == ["bar", "plain"]
    # Dict
    assert interpolate_value({"k1": "${{ foo }}", "k2": "plain"}, vars) == {
        "k1": "bar",
        "k2": "plain",
    }


def test_interpolate_value_syntax_error_raises():
    vars = {"foo": "bar"}
    # Invalid expression with unclosed brackets or mismatched operators
    bad_expr = "${{ foo + }}"
    with pytest.raises(UserException) as excinfo:
        interpolate_value(bad_expr, vars)
    assert "Jinja template syntax error in expression" in str(excinfo.value)
    assert "unexpected" in str(excinfo.value).lower()
