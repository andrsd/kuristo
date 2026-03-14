import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from kuristo.__main__ import main
from kuristo.workflow import get_job_ids_for_labels, parse_workflow_files

ASSETS_DIR = Path(__file__).parent / "assets"
TEST_LABELS_YAML = ASSETS_DIR / "test_labels" / "ktests.yaml"


class TestGetJobIdsForLabels:
    """Test the get_job_ids_for_labels utility function"""

    @pytest.fixture
    def workflows(self):
        """Load test workflows"""
        return parse_workflow_files([TEST_LABELS_YAML])

    def test_no_labels_returns_empty_set(self, workflows):
        """Test that no labels returns empty set"""
        result = get_job_ids_for_labels(workflows, [])
        assert result == set()

    def test_smoke_label_includes_smoke_tests(self, workflows):
        """Test smoke label includes smoke-test-1 and smoke-test-2"""
        result = get_job_ids_for_labels(workflows, ["smoke"])
        assert "smoke-test-1" in result
        assert "smoke-test-2" in result
        assert "integration-test" not in result
        assert "free-job" not in result
        assert "i-need-free-job" not in result

    def test_quick_label_includes_transitive_dependencies(self, workflows):
        """Test quick label includes smoke-test-1, i-need-free-job, and their dependency free-job"""
        result = get_job_ids_for_labels(workflows, ["quick"])
        # smoke-test-1 and i-need-free-job have 'quick' label
        assert "smoke-test-1" in result
        assert "i-need-free-job" in result
        # free-job is a dependency of i-need-free-job
        assert "free-job" in result
        # smoke-test-2 doesn't have 'quick' label
        assert "smoke-test-2" not in result
        assert "integration-test" not in result

    def test_multiple_labels_union(self, workflows):
        """Test multiple labels are treated as union"""
        result = get_job_ids_for_labels(workflows, ["smoke", "quick"])
        # Jobs with smoke label
        assert "smoke-test-1" in result
        assert "smoke-test-2" in result
        # Jobs with quick label
        assert "i-need-free-job" in result
        # Dependency of quick-labeled jobs
        assert "free-job" in result
        # No other jobs
        assert "integration-test" not in result

    def test_integration_label(self, workflows):
        """Test integration label"""
        result = get_job_ids_for_labels(workflows, ["integration"])
        assert "integration-test" in result
        # No dependencies for integration-test
        assert len(result) == 1

    def test_nonexistent_label_returns_empty(self, workflows):
        """Test nonexistent label returns empty set"""
        result = get_job_ids_for_labels(workflows, ["nonexistent"])
        assert result == set()


class TestLabelFilteringCLI:
    """Test label filtering in CLI commands"""

    def test_list_all_jobs_no_label(self, capsys):
        """Test list command without label filter shows all jobs"""
        test_argv = ["kuristo", "--no-ansi", "list", str(ASSETS_DIR / "test_labels")]
        with patch.object(sys, "argv", test_argv):
            main()

        captured = capsys.readouterr()
        # Should show all jobs
        assert "smoke-test-1" in captured.out
        assert "smoke-test-2" in captured.out
        assert "integration-test" in captured.out
        assert "free-job" in captured.out
        assert "i-need-free-job" in captured.out

    def test_list_smoke_label(self, capsys):
        """Test list command with smoke label filter"""
        test_argv = [
            "kuristo",
            "--no-ansi",
            "list",
            "--label",
            "smoke",
            str(ASSETS_DIR / "test_labels"),
        ]
        with patch.object(sys, "argv", test_argv):
            main()

        captured = capsys.readouterr()
        # Should show only smoke-labeled jobs
        assert "smoke-test-1" in captured.out
        assert "smoke-test-2" in captured.out
        # Should not show non-smoke jobs
        assert "integration-test" not in captured.out
        assert "free-job" not in captured.out
        assert "i-need-free-job" not in captured.out

    def test_list_quick_label(self, capsys):
        """Test list command with quick label filter"""
        test_argv = [
            "kuristo",
            "--no-ansi",
            "list",
            "--label",
            "quick",
            str(ASSETS_DIR / "test_labels"),
        ]
        with patch.object(sys, "argv", test_argv):
            main()

        captured = capsys.readouterr()
        # Should show quick-labeled jobs
        assert "smoke-test-1" in captured.out
        assert "i-need-free-job" in captured.out
        # Should not show other jobs
        assert "smoke-test-2" not in captured.out
        assert "integration-test" not in captured.out
        # free-job is a dependency so it should be included
        assert "free-job" in captured.out

    def test_list_multiple_labels(self, capsys):
        """Test list command with multiple label filters"""
        test_argv = [
            "kuristo",
            "--no-ansi",
            "list",
            "--label",
            "smoke",
            "--label",
            "quick",
            str(ASSETS_DIR / "test_labels"),
        ]
        with patch.object(sys, "argv", test_argv):
            main()

        captured = capsys.readouterr()
        # Should show jobs matching either label
        assert "smoke-test-1" in captured.out
        assert "smoke-test-2" in captured.out
        assert "i-need-free-job" in captured.out
        assert "free-job" in captured.out
        # integration-test has neither label
        assert "integration-test" not in captured.out
