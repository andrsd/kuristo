import subprocess
import tempfile
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"


def test_rerun_failed_basic():
    """Test that --rerun-failed flag is recognized and can run"""
    test_dir = ASSETS_DIR / "tests1"

    with tempfile.TemporaryDirectory() as tmpdir:
        import os

        env = os.environ.copy()
        env["KURISTO_LOG_DIR"] = tmpdir

        # First run - should succeed
        result = subprocess.run(
            ["kuristo", "--no-ansi", "run", str(test_dir)],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0
        assert "Success: 2" in result.stdout

        # Second run with --rerun-failed - should fail because no jobs failed
        result = subprocess.run(
            ["kuristo", "--no-ansi", "run", "--rerun-failed", str(test_dir)],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 1
        assert "No failed jobs found" in result.stdout


def test_rerun_failed_with_actual_failures():
    """Test that --rerun-failed correctly identifies and re-runs failed jobs"""
    test_dir = ASSETS_DIR / "tests3"

    # First run - will have failures
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Failed: 1" in result.stdout

    # Second run with --rerun-failed - should detect the failed job
    # Since the test is designed to always fail, this will fail again
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", "--rerun-failed", str(test_dir)],
        capture_output=True,
        text=True,
    )
    # The important thing is that it ran and detected the failed job from the previous run
    # It will fail again because the job is designed to fail
    assert "Failed: 1" in result.stdout or "test-that-fails" in result.stdout
