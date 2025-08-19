import pytest
from unittest.mock import patch, MagicMock
from kuristo.cli._status import summarize, print_report, status


def test_summarize_counts_correctly():
    results = [
        {"status": "success"},
        {"status": "failed"},
        {"status": "failed"},
        {"status": "skipped"},
        {"status": "success"},
    ]

    with patch("kuristo.cli._status.ui.RunStats") as mock_stats:
        summarize(results)
        mock_stats.assert_called_once_with(2, 2, 1)  # success, failed, skipped


@patch("kuristo.cli._status.ui.status_line")
@patch("kuristo.cli._status.ui.line")
@patch("kuristo.cli._status.ui.stats")
@patch("kuristo.cli._status.ui.time")
@patch("kuristo.cli._status.ui.RunStats")
@patch("kuristo.cli._status.config.get")
def test_print_report_outputs_correctly(
    mock_config_get, mock_RunStats, mock_time, mock_stats, mock_line, mock_status_line
):
    report = {
        "results": [
            {"status": "success", "job-name": "Test A"},
            {"status": "failed", "job-name": "Another"},
        ],
        "total-runtime": 12.34
    }

    mock_cfg = MagicMock()
    mock_cfg.console_width = 20
    mock_config_get.return_value = mock_cfg

    print_report(report, [])

    # Check status_line called per entry
    assert mock_status_line.call_count == 2
    mock_line.assert_called_once()
    mock_stats.assert_called_once()
    mock_time.assert_called_once_with(12.34)
    mock_RunStats.assert_called_once_with(1, 1, 0)


@patch("kuristo.cli._status.ui.status_line")
@patch("kuristo.cli._status.ui.line")
@patch("kuristo.cli._status.ui.stats")
@patch("kuristo.cli._status.ui.time")
@patch("kuristo.cli._status.ui.RunStats")
@patch("kuristo.cli._status.config.get")
def test_print_report_outputs_filtered(
    mock_config_get, mock_RunStats, mock_time, mock_stats, mock_line, mock_status_line
):
    report = {
        "results": [
            {"status": "success", "job-name": "Test A"},
            {"status": "success", "job-name": "Test B"},
            {"status": "failed", "job-name": "Another"},
        ],
        "total-runtime": 12.34
    }

    mock_cfg = MagicMock()
    mock_cfg.console_width = 20
    mock_config_get.return_value = mock_cfg

    print_report(report, ["failed"])

    # Check status_line called per entry
    assert mock_status_line.call_count == 1
    mock_line.assert_called_once()
    mock_stats.assert_called_once()
    mock_time.assert_called_once_with(12.34)
    mock_RunStats.assert_called_once_with(0, 1, 0)


@patch("kuristo.cli._status.print_report")
@patch("kuristo.cli._status.utils.read_report")
@patch("kuristo.cli._status.config.get")
def test_status_reads_report_and_calls_print(mock_cfg_get, mock_read_report, mock_print_report, tmp_path):
    report_path = tmp_path / "runs" / "latest" / "report.yaml"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("fake: data")

    mock_cfg = MagicMock()
    mock_cfg.log_dir = tmp_path
    mock_cfg_get.return_value = mock_cfg

    expected_report = {"results": [{"status": "success", "job-name": "Job X"}]}
    expected_filters = []
    mock_read_report.return_value = expected_report

    args = MagicMock()
    args.run_id = None
    args.failed = False
    args.skipped = False
    args.passed = False

    status(args)

    mock_read_report.assert_called_once_with(report_path)
    mock_print_report.assert_called_once_with(expected_report, expected_filters)


@patch("kuristo.cli._status.config.get")
def test_status_missing_report_raises(mock_cfg_get, tmp_path):
    mock_cfg = MagicMock()
    mock_cfg.log_dir = tmp_path
    mock_cfg_get.return_value = mock_cfg

    args = MagicMock()
    args.run = None

    with pytest.raises(RuntimeError, match="No report found"):
        status(args)
