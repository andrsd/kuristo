import pytest
from unittest.mock import patch, MagicMock
from kuristo.cli._log import log


@patch("kuristo.cli._log.ui.console")
@patch("kuristo.cli._log.config.get")
@patch("kuristo.cli._log.utils.read_report")
def test_log_with_runs(mock_read_report, mock_config_get, mock_console, tmp_path):
    # Setup fake directory structure
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    run1 = runs_dir / "0001"
    run1.mkdir()
    run2 = runs_dir / "0002"
    run2.mkdir()
    (runs_dir / "latest").symlink_to(run2)

    # Add report files
    report1 = run1 / "report.yaml"
    report1.write_text("fake")
    report2 = run2 / "report.yaml"
    report2.write_text("fake")

    # Mock config.get()
    mock_cfg = MagicMock()
    mock_cfg.log_dir = tmp_path
    mock_config_get.return_value = mock_cfg

    # Mock read_report() to simulate report content
    mock_read_report.side_effect = [
        {"results": ["job1", "job2"], "total-runtime": 0.123},
        {"results": ["job1"], "total-runtime": 0.456},
    ]

    # Mock console
    mock_console_instance = MagicMock()
    mock_console.return_value = mock_console_instance

    # Call the function
    log(args={})

    # Assert table was printed with expected data
    assert mock_console_instance.print.called
    table = mock_console_instance.print.call_args[0][0]
    assert hasattr(table, "add_row")

    rows = table.rows
    assert len(rows) == 2


@patch("kuristo.cli._log.ui.console")
@patch("kuristo.cli._log.config.get")
def test_log_no_runs(mock_config_get, mock_console, tmp_path):
    # runs/ doesn't exist
    mock_cfg = MagicMock()
    mock_cfg.log_dir = tmp_path
    mock_config_get.return_value = mock_cfg

    # Expect RuntimeError due to missing runs/
    with pytest.raises(RuntimeError, match="No runs found."):
        log(args={})
