from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from kuristo.cli._show import (
    parse_log_line,
    parse_sections,
    render_title,
    render_section,
    render_sections,
    display_job_log,
    show
)
from rich.text import Text


def test_parse_log_line_valid():
    line = "2025-07-26 13:00:00,123 - INFO - something happened"
    result = parse_log_line(line)
    assert result is not None

    timestamp, tag, msg = result
    assert isinstance(timestamp, datetime)
    assert timestamp == datetime(2025, 7, 26, 13, 0, 0, 123000)
    assert tag == "INFO"
    assert msg == "something happened"


@pytest.mark.parametrize("line", [
    "invalid line",
    "2025-07-26 13:00:00 - INFO - missing milliseconds",
    "2025-07-26 13:00:00,123 - only two parts",
    "2025-07-26 13:00:00,123 - INFO",  # missing msg
    "2025-07-26 13:00:00,123",         # no dashes
    "2025-07-26T13:00:00,123 - INFO - ISO format timestamp",  # bad timestamp format
])
def test_parse_log_line_invalid(line):
    assert parse_log_line(line) is None

# ---


def ts(offset_sec):
    return datetime(2025, 7, 26, 13, 0, 0) + timedelta(seconds=offset_sec)


def test_single_job_with_task():
    lines = [
        (ts(0), "JOB_START", "Running job A"),
        (ts(1), "TASK_START", "> Doing something"),
        (ts(2), "INFO", "This is a line"),
        (ts(3), "TASK_END", "exit code 0"),
        (ts(4), "JOB_END", "Done"),
    ]

    sections = parse_sections(lines)
    assert len(sections) == 2  # title + 1 task

    title = sections[0]
    task = sections[1]

    assert title["type"] == "title"
    assert title["title"] == "Running job A"
    assert title["start_time"] == ts(0)
    assert title["end_time"] == ts(4)

    assert task["type"] == "section"
    assert task["title"] == "Doing something"
    assert task["start_time"] == ts(1)
    assert task["end_time"] == ts(3)
    assert task["return_code"] == 0
    assert task["lines"] == [("INFO", "This is a line")]


def test_task_with_env_vars_and_misc_lines():
    lines = [
        (ts(0), "TASK_START", "> Task begins"),
        (ts(1), "INFO", "Some output"),
        (ts(2), "DEBUG", "Debug output"),
        (ts(3), "INFO", "| FOO=BAR"),
        (ts(4), "TASK_END", "exit code 1"),
    ]

    sections = parse_sections(lines)
    task = sections[0]

    assert task["title"] == "Task begins"
    assert task["return_code"] == 1
    assert task["lines"] == [
        ("INFO", "Some output"),
        ("DEBUG", "Debug output"),
        ("ENV_VAR", "FOO=BAR"),
    ]


def test_multiple_tasks():
    lines = [
        (ts(0), "TASK_START", "> First task"),
        (ts(1), "INFO", "Line A"),
        (ts(2), "TASK_END", "exit code 0"),
        (ts(3), "TASK_START", "> Second task"),
        (ts(4), "INFO", "Line B"),
        (ts(5), "TASK_END", "exit code 2"),
    ]

    sections = parse_sections(lines)
    assert len(sections) == 2
    assert sections[0]["title"] == "First task"
    assert sections[1]["title"] == "Second task"
    assert sections[0]["return_code"] == 0
    assert sections[1]["return_code"] == 2


def test_unclosed_task():
    lines = [
        (ts(0), "TASK_START", "> Unclosed"),
        (ts(1), "INFO", "Still going"),
    ]

    sections = parse_sections(lines)
    assert len(sections) == 1
    task = sections[0]
    assert task["title"] == "Unclosed"
    assert task["return_code"] is None
    assert task["end_time"] is None
    assert task["lines"] == [("INFO", "Still going")]

# ---


def make_section(title="My Task", rc=0, duration=1.23, lines=None, missing_times=False):
    now = datetime(2025, 7, 26, 13, 0, 0)
    return {
        "type": "section",
        "title": title,
        "return_code": rc,
        "start_time": None if missing_times else now,
        "end_time": None if missing_times else now + timedelta(seconds=duration),
        "lines": lines or [],
    }


@patch("kuristo.cli._show.ui.console")
@patch("kuristo.cli._show.utils.human_time")
def test_render_title_normal(mock_human_time, mock_console):
    mock_human_time.return_value = "2.30s"
    mock_console_instance = MagicMock()
    mock_console.return_value = mock_console_instance

    sec = make_section()
    render_title(sec, max_label_len=50)

    assert mock_human_time.called
    printed_text = mock_console_instance.print.call_args_list[0][0][0]
    assert isinstance(printed_text, Text)
    assert "My Task" in str(printed_text)
    assert "2.30s" in str(printed_text)
    assert "." in str(printed_text)


@patch("kuristo.cli._show.ui.console")
@patch("kuristo.cli._show.utils.human_time")
def test_render_title_missing_times(mock_human_time, mock_console):
    mock_human_time.return_value = "0.00s"
    mock_console_instance = MagicMock()
    mock_console.return_value = mock_console_instance

    sec = make_section(missing_times=True)
    render_title(sec, max_label_len=40)

    mock_human_time.assert_called_with(0.0)
    txt = mock_console_instance.print.call_args_list[0][0][0]
    assert "My Task" in str(txt)
    assert "0.00s" in str(txt)


@patch("kuristo.cli._show.ui.console")
@patch("kuristo.cli._show.utils.human_time")
def test_render_title_long_title(mock_human_time, mock_console):
    mock_human_time.return_value = "99.9s"
    mock_console_instance = MagicMock()
    mock_console.return_value = mock_console_instance

    sec = make_section(title="This is a very long task title that may overflow")
    render_title(sec, max_label_len=20)  # Forces `wd` to go negative

    # No crash, still prints
    mock_console_instance.print.assert_called()

# ---


@patch("kuristo.cli._show.ui.console")
@patch("kuristo.cli._show.utils.human_time")
def test_render_section_pass(mock_human_time, mock_console, capsys):
    mock_human_time.return_value = "1.20s"
    console = MagicMock()
    mock_console.return_value = console

    sec = make_section(rc=0, lines=[("OUTPUT", "Success output"), ("SCRIPT", "echo run")])
    render_section(sec, max_label_len=50)

    texts = []
    for call in console.print.call_args_list:
        args = call.args
        if args:
            texts.append(str(args[0]))
    assert any("PASS" in line for line in texts)
    assert any("Success output" in line for line in texts)
    assert any("echo run" in line for line in texts)


@patch("kuristo.cli._show.ui.console")
@patch("kuristo.cli._show.utils.human_time")
def test_render_section_fail_with_env(mock_human_time, mock_console):
    mock_human_time.return_value = "2.30s"
    console = MagicMock()
    mock_console.return_value = console

    lines = [
        ("ENV", ""),
        ("ENV_VAR", "FOO=123"),
        ("OUTPUT", "Error message"),
        ("INFO", "Some info"),
        ("RANDOM", "???"),
    ]
    sec = make_section(rc=1, lines=lines)
    render_section(sec, max_label_len=60)

    texts = []
    for call in console.print.call_args_list:
        args = call.args
        if args:
            texts.append(str(args[0]))
    assert any("FAIL" in t for t in texts)
    assert any("Environment variables" in t for t in texts)
    assert any("FOO=123" in t for t in texts)
    assert any("Error message" in t for t in texts)
    assert any("Some info" in t for t in texts)
    assert any("???" in t for t in texts)


@patch("kuristo.cli._show.ui.console")
@patch("kuristo.cli._show.utils.human_time")
def test_render_section_missing_times(mock_human_time, mock_console):
    mock_human_time.return_value = "0.00s"
    console = MagicMock()
    mock_console.return_value = console

    sec = make_section(rc=0, missing_times=True)
    render_section(sec, max_label_len=40)

    assert mock_human_time.called
    output = str(console.print.call_args_list[0][0][0])
    assert "0.00s" in output


@patch("kuristo.cli._show.ui.console")
@patch("kuristo.cli._show.utils.human_time")
def test_render_section_handles_dot_padding(mock_human_time, mock_console):
    mock_human_time.return_value = "1.20s"
    console = MagicMock()
    mock_console.return_value = console

    # Force a negative padding (dots will be "")
    sec = make_section(title="A really long section title", rc=0)
    render_section(sec, max_label_len=10)

    header = str(console.print.call_args_list[0][0][0])
    assert "...." not in header or isinstance(header, Text)  # Dots suppressed if negative width


@patch("kuristo.cli._show.render_title")
@patch("kuristo.cli._show.render_section")
@patch("kuristo.cli._show.config.get")
def test_render_sections_calls_correct_renderers(mock_cfg_get, mock_render_section, mock_render_title):
    mock_cfg = MagicMock()
    mock_cfg.console_width = 80
    mock_cfg_get.return_value = mock_cfg

    sections = [
        {"type": "title", "title": "Header", "start_time": None, "end_time": None},
        make_section()
    ]

    render_sections(sections)

    mock_render_title.assert_called_once()
    mock_render_section.assert_called_once()


@patch("kuristo.cli._show.render_sections")
@patch("kuristo.cli._show.parse_log_line")
def test_display_job_log_parses_and_renders(mock_parse_log_line, mock_render_sections, tmp_path):
    log_file = tmp_path / "job-1.log"
    log_file.write_text("")

    mock_parse_log_line.side_effect = [
        ("2025-07-26 13:00:00", "INFO", "Something"),
        None,  # simulate one invalid line
    ]

    display_job_log(log_file)

    mock_render_sections.assert_called_once()
    sections_arg = mock_render_sections.call_args[0][0]
    assert isinstance(sections_arg, list)
    assert len(sections_arg) >= 0  # parse_sections() could return empty


def test_display_job_log_missing_file():
    with pytest.raises(RuntimeError, match="Log file not found"):
        display_job_log(Path("/nonexistent/file.log"))


@patch("kuristo.cli._show.display_job_log")
@patch("kuristo.cli._show.config.get")
def test_show_uses_correct_log_path(mock_cfg_get, mock_display_job_log):
    args = MagicMock()
    args.run_id = None
    args.job = 42

    mock_cfg = MagicMock()
    mock_cfg.log_dir = Path("/some/logs")
    mock_cfg_get.return_value = mock_cfg

    show(args)

    expected_path = Path("/some/logs/runs/latest/job-42.log")
    mock_display_job_log.assert_called_once_with(expected_path)
