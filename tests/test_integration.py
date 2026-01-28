import subprocess
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"


def test_traversal():
    test_dir = ASSETS_DIR / "tests1"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Success: 2" in result.stdout
    assert "Total: 2" in result.stdout


def test_multiple_in_one_file():
    test_dir = ASSETS_DIR / "tests2"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Success: 3" in result.stdout
    assert "Skipped: 2" in result.stdout
    assert "Total: 5" in result.stdout


def test_failed():
    test_dir = ASSETS_DIR / "tests3"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Success: 4" in result.stdout
    assert "Failed: 1" in result.stdout
    assert "Skipped: 0" in result.stdout
    assert "Total: 5" in result.stdout


def test_user_defined():
    test_dir = ASSETS_DIR / "tests5"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Success: 1" in result.stdout
    assert "Failed: 0" in result.stdout
    assert "Skipped: 0" in result.stdout
    assert "Total: 1" in result.stdout


def test_exodiff():
    test_dir = ASSETS_DIR / "tests6"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Success: 1" in result.stdout
    assert "Failed: 0" in result.stdout
    assert "Skipped: 0" in result.stdout
    assert "Total: 1" in result.stdout


def test_deps():
    test_dir = ASSETS_DIR / "tests7"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Success: 3" in result.stdout
    assert "Failed: 0" in result.stdout
    assert "Skipped: 0" in result.stdout
    assert "Total: 3" in result.stdout


def test_env():
    test_dir = ASSETS_DIR / "tests8"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Success: 3" in result.stdout
    assert "Failed: 0" in result.stdout
    assert "Skipped: 0" in result.stdout
    assert "Total: 3" in result.stdout


def test_matrix():
    test_dir = ASSETS_DIR / "tests10"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Success: 9" in result.stdout
    assert "Failed: 0" in result.stdout
    assert "Skipped: 0" in result.stdout
    assert "Total: 9" in result.stdout


def test_float_check_str():
    test_dir = ASSETS_DIR / "tests4"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Success: 0" in result.stdout
    assert "Failed: 1" in result.stdout
    assert "Skipped: 0" in result.stdout
    assert "Total: 1" in result.stdout


def test_convergence():
    test_dir = ASSETS_DIR / "tests12"
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(test_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Success: 2" in result.stdout
    assert "Failed: 0" in result.stdout
    assert "Skipped: 0" in result.stdout
    assert "Total: 2" in result.stdout
