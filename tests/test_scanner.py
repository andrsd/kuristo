import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from kuristo.scanner import Scanner, scan_locations  # adjust import path


@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.workflow_filename = "workflow.yml"
    with patch("kuristo.scanner.config.get", return_value=cfg):
        yield cfg


def test_scanner_location_property(mock_config):
    scanner = Scanner("/some/path")
    assert scanner.location == "/some/path"


def test_scanner_scan_finds_files(mock_config):
    with patch("os.walk") as mock_walk:
        mock_walk.return_value = [
            ("/some/path", ["dir1"], ["workflow.yml", "other.txt"]),
            ("/some/path/dir1", [], ["workflow.yml"])
        ]
        scanner = Scanner("/some/path")
        results = scanner.scan()
        assert results == [
            Path("/some/path/workflow.yml"),
            Path("/some/path/dir1/workflow.yml")
        ]


def test_scanner_scan_no_files(mock_config):
    with patch("os.walk", return_value=[("/some/path", [], ["other.txt"])]):
        scanner = Scanner("/some/path")
        results = scanner.scan()
        assert results == []


def test_scan_locations_with_directory(mock_config):
    with patch("os.path.isdir", return_value=True), \
         patch("os.walk", return_value=[("/loc", [], ["workflow.yml"])]):
        results = scan_locations(["/loc"])
        assert results == [Path("/loc/workflow.yml")]


def test_scan_locations_with_file(mock_config):
    with patch("os.path.isfile", return_value=True), \
         patch("os.path.isdir", return_value=False):
        results = scan_locations(["/file/path"])
        assert results == [Path("/file/path")]


def test_scan_locations_invalid_path_raises(mock_config):
    with patch("os.path.isfile", return_value=False), \
         patch("os.path.isdir", return_value=False):
        with pytest.raises(RuntimeError) as excinfo:
            scan_locations(["/bad/path"])
        assert "No such file or directory" in str(excinfo.value)
