import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from kuristo.cli._diff import diff
from kuristo.exceptions import UserException


# Helper function to create mock report data
def create_mock_report(
    version: str,
    results: list,
    total_runtime: float = 0.0,
):
    return {
        "version": version,
        "results": results,
        "total-runtime": total_runtime,
    }


@patch("kuristo.cli._diff.ui.console")
@patch("kuristo.cli._diff.utils.get_run_output_dir")
@patch("kuristo.cli._diff.utils.resolve_run_id")
@patch("kuristo.cli._diff.utils.read_report")
@patch("kuristo.cli._diff.config.get")
def test_diff_same_reports(
    mock_config_get,
    mock_read_report,
    mock_resolve_run_id,
    mock_get_run_output_dir,
    mock_console,
    tmp_path,
):
    # Setup mocks
    mock_config_get.return_value.log_dir = tmp_path
    mock_resolve_run_id.side_effect = ["run_id_1", "run_id_2"]

    # Create mock run directories that have a mock .exists() method
    mock_run_dir_1 = MagicMock(spec=Path)
    mock_run_dir_1.name = "run_id_1"
    mock_run_dir_1.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml
    mock_run_dir_2 = MagicMock(spec=Path)
    mock_run_dir_2.name = "run_id_2"
    mock_run_dir_2.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml

    mock_get_run_output_dir.side_effect = [mock_run_dir_1, mock_run_dir_2]

    report_data = create_mock_report(
        "0.12.2",
        [
            {
                "id": 1,
                "job-name": "jobA",
                "workflow-file": "wf1.yaml",
                "status": "success",
                "duration": 10.0,
            },
            {
                "id": 2,
                "job-name": "jobB",
                "workflow-file": "wf1.yaml",
                "status": "failed",
                "duration": 5.0,
            },
        ],
    )
    mock_read_report.side_effect = [report_data, report_data]

    # Use a StringIO to capture the actual console output
    output_buffer = io.StringIO()
    mock_console_instance = Console(file=output_buffer, no_color=True)
    mock_console.return_value = mock_console_instance

    args = MagicMock(run1="latest", run2="tagA")
    exit_code = diff(args)

    assert exit_code == 0
    # Get the captured output
    table_str = output_buffer.getvalue()
    assert "No difference" in table_str


@patch("kuristo.cli._diff.ui.console")
@patch("kuristo.cli._diff.utils.get_run_output_dir")
@patch("kuristo.cli._diff.utils.resolve_run_id")
@patch("kuristo.cli._diff.utils.read_report")
@patch("kuristo.cli._diff.config.get")
def test_diff_different_durations(
    mock_config_get,
    mock_read_report,
    mock_resolve_run_id,
    mock_get_run_output_dir,
    mock_console,
    tmp_path,
):
    # Setup mocks
    mock_config_get.return_value.log_dir = tmp_path
    mock_resolve_run_id.side_effect = ["run_id_1", "run_id_2"]

    # Create mock run directories that have a mock .exists() method
    mock_run_dir_1 = MagicMock(spec=Path)
    mock_run_dir_1.name = "run_id_1"
    mock_run_dir_1.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml
    mock_run_dir_2 = MagicMock(spec=Path)
    mock_run_dir_2.name = "run_id_2"
    mock_run_dir_2.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml

    mock_get_run_output_dir.side_effect = [mock_run_dir_1, mock_run_dir_2]

    report1_data = create_mock_report(
        "0.12.2",
        [
            {
                "id": 1,
                "job-name": "jobA",
                "workflow-file": "wf1.yaml",
                "status": "success",
                "duration": 10.0,
                "return-code": 0,
            }
        ],
    )
    report2_data = create_mock_report(
        "0.12.2",
        [
            {
                "id": 1,
                "job-name": "jobA",
                "workflow-file": "wf1.yaml",
                "status": "failed",
                "duration": 12.5,
                "return-code": 1,
            }
        ],
    )
    mock_read_report.side_effect = [report1_data, report2_data]

    # Use a StringIO to capture the actual console output
    output_buffer = io.StringIO()
    mock_console_instance = Console(file=output_buffer, no_color=True)
    mock_console.return_value = mock_console_instance

    args = MagicMock(run1="latest", run2="tagA")
    exit_code = diff(args)

    assert exit_code == 0
    # Get the captured output
    table_str = output_buffer.getvalue()
    assert "jobA" in table_str
    assert "PASS: 0" in table_str
    assert "FAIL: 1" in table_str
    assert "10.00s" in table_str
    assert "12.50s" in table_str


@patch("kuristo.cli._diff.ui.console")
@patch("kuristo.cli._diff.utils.get_run_output_dir")
@patch("kuristo.cli._diff.utils.resolve_run_id")
@patch("kuristo.cli._diff.utils.read_report")
@patch("kuristo.cli._diff.config.get")
def test_diff_jobs_in_one_report_only(
    mock_config_get,
    mock_read_report,
    mock_resolve_run_id,
    mock_get_run_output_dir,
    mock_console,
    tmp_path,
):
    # Setup mocks
    mock_config_get.return_value.log_dir = tmp_path
    mock_resolve_run_id.side_effect = ["run_id_1", "run_id_2"]

    # Create mock run directories that have a mock .exists() method
    mock_run_dir_1 = MagicMock(spec=Path)
    mock_run_dir_1.name = "run_id_1"
    mock_run_dir_1.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml
    mock_run_dir_2 = MagicMock(spec=Path)
    mock_run_dir_2.name = "run_id_2"
    mock_run_dir_2.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml

    mock_get_run_output_dir.side_effect = [mock_run_dir_1, mock_run_dir_2]

    report1_data = create_mock_report(
        "0.12.2",
        [
            {
                "id": 1,
                "job-name": "jobA",
                "workflow-file": "wf1.yaml",
                "status": "success",
                "duration": 10.0,
                "return-code": 0,
            }
        ],
    )
    report2_data = create_mock_report(
        "0.12.2",
        [
            {
                "id": 2,
                "job-name": "jobB",
                "workflow-file": "wf1.yaml",
                "status": "success",
                "duration": 5.0,
                "return-code": 0,
            }
        ],
    )
    mock_read_report.side_effect = [report1_data, report2_data]

    # Use a StringIO to capture the actual console output
    output_buffer = io.StringIO()
    mock_console_instance = Console(file=output_buffer, no_color=True)
    mock_console.return_value = mock_console_instance

    args = MagicMock(run1="latest", run2="tagA")
    exit_code = diff(args)

    assert exit_code == 0
    # Get the captured output
    table_str = output_buffer.getvalue()
    # JobA only in report 1
    assert "jobA" in table_str
    assert "10.00s" in table_str

    # JobB only in report 2
    assert "jobB" in table_str
    assert "5.00s" in table_str

    assert table_str.count("PASS: 0") == 2


@patch("kuristo.cli._diff.utils.get_run_output_dir")
@patch("kuristo.cli._diff.utils.resolve_run_id")
@patch("kuristo.cli._diff.utils.read_report")
@patch("kuristo.cli._diff.config.get")
def test_diff_report_missing_version(
    mock_config_get,
    mock_read_report,
    mock_resolve_run_id,
    mock_get_run_output_dir,
    tmp_path,
):
    # Setup mocks
    mock_config_get.return_value.log_dir = tmp_path
    mock_resolve_run_id.side_effect = ["run_id_1", "run_id_2"]

    # Create mock run directories that have a mock .exists() method
    mock_run_dir_1 = MagicMock(spec=Path)
    mock_run_dir_1.name = "run_id_1"
    mock_run_dir_1.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml
    mock_run_dir_2 = MagicMock(spec=Path)
    mock_run_dir_2.name = "run_id_2"
    mock_run_dir_2.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml

    mock_get_run_output_dir.side_effect = [mock_run_dir_1, mock_run_dir_2]

    report1_data = {"results": [], "total-runtime": 0.0}  # Missing version
    report2_data = create_mock_report("0.12.2", [])
    mock_read_report.side_effect = [report1_data, report2_data]

    args = MagicMock(run1="latest", run2="tagA")

    with pytest.raises(UserException) as excinfo:
        diff(args)

    assert "does not specify a kuristo version" in str(excinfo.value)


@patch("kuristo.cli._diff.utils.get_run_output_dir")
@patch("kuristo.cli._diff.utils.resolve_run_id")
@patch("kuristo.cli._diff.utils.read_report")
@patch("kuristo.cli._diff.config.get")
def test_diff_report_old_version(
    mock_config_get,
    mock_read_report,
    mock_resolve_run_id,
    mock_get_run_output_dir,
    tmp_path,
):
    # Setup mocks
    mock_config_get.return_value.log_dir = tmp_path
    mock_resolve_run_id.side_effect = ["run_id_1", "run_id_2"]

    # Create mock run directories that have a mock .exists() method
    mock_run_dir_1 = MagicMock(spec=Path)
    mock_run_dir_1.name = "run_id_1"
    mock_run_dir_1.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml
    mock_run_dir_2 = MagicMock(spec=Path)
    mock_run_dir_2.name = "run_id_2"
    mock_run_dir_2.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml

    mock_get_run_output_dir.side_effect = [mock_run_dir_1, mock_run_dir_2]

    report1_data = create_mock_report("0.12.1", [])  # Old version
    report2_data = create_mock_report("0.12.2", [])
    mock_read_report.side_effect = [report1_data, report2_data]

    args = MagicMock(run1="latest", run2="tagA")

    with pytest.raises(UserException) as excinfo:
        diff(args)

    assert "is too old" in str(excinfo.value)


@patch("kuristo.cli._diff.utils.get_run_output_dir")
@patch("kuristo.cli._diff.utils.resolve_run_id")
@patch("kuristo.cli._diff.utils.read_report")
@patch("kuristo.cli._diff.config.get")
def test_diff_report_file_not_found(
    mock_config_get,
    mock_read_report,
    mock_resolve_run_id,
    mock_get_run_output_dir,
    tmp_path,
):
    # Setup mocks
    mock_config_get.return_value.log_dir = tmp_path
    mock_resolve_run_id.side_effect = ["run_id_1", "run_id_2"]

    # Create mock run directories that have a mock .exists() method
    mock_run_dir_1 = MagicMock(spec=Path)
    mock_run_dir_1.name = "run_id_1"
    mock_run_dir_1.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml
    mock_run_dir_2 = MagicMock(spec=Path)
    mock_run_dir_2.name = "run_id_2"
    mock_run_dir_2_report_path_mock = MagicMock(spec=Path, exists=MagicMock(return_value=False))
    mock_run_dir_2.__truediv__.return_value = mock_run_dir_2_report_path_mock  # For report.yaml

    mock_get_run_output_dir.side_effect = [mock_run_dir_1, mock_run_dir_2]

    report1_data = create_mock_report("0.12.2", [])
    mock_read_report.return_value = report1_data

    args = MagicMock(run1="latest", run2="tagA")
    with pytest.raises(UserException) as excinfo:
        diff(args)

    assert "Report file not found" in str(excinfo.value)


# Test with tags (resolve_run_id should be called)
@patch("kuristo.cli._diff.ui.console")
@patch("kuristo.cli._diff.utils.get_run_output_dir")
@patch("kuristo.cli._diff.utils.resolve_run_id")
@patch("kuristo.cli._diff.utils.read_report")
@patch("kuristo.cli._diff.config.get")
def test_diff_with_tags(
    mock_config_get,
    mock_read_report,
    mock_resolve_run_id,
    mock_get_run_output_dir,
    mock_console,
    tmp_path,
):
    # Setup mocks
    mock_config_get.return_value.log_dir = tmp_path
    mock_resolve_run_id.side_effect = ["resolved_run_id_1", "resolved_run_id_2"]

    # Create mock run directories that have a mock .exists() method
    mock_run_dir_1 = MagicMock(spec=Path)
    mock_run_dir_1.name = "resolved_run_id_1"
    mock_run_dir_1.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml
    mock_run_dir_2 = MagicMock(spec=Path)
    mock_run_dir_2.name = "resolved_run_id_2"
    mock_run_dir_2.__truediv__.return_value = MagicMock(
        spec=Path, exists=MagicMock(return_value=True)
    )  # For report.yaml

    mock_get_run_output_dir.side_effect = [mock_run_dir_1, mock_run_dir_2]

    report_data = create_mock_report("0.12.2", [])
    mock_read_report.side_effect = [report_data, report_data]

    # Use a StringIO to capture the actual console output
    output_buffer = io.StringIO()
    mock_console_instance = Console(file=output_buffer, no_color=True)
    mock_console.return_value = mock_console_instance

    args = MagicMock(run1="tag_latest", run2="tag_v1")
    exit_code = diff(args)

    assert exit_code == 0
    assert mock_resolve_run_id.call_count == 2
    mock_resolve_run_id.assert_any_call(tmp_path, "tag_latest")
    mock_resolve_run_id.assert_any_call(tmp_path, "tag_v1")
