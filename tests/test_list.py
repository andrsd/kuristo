import sys
import re
from pathlib import Path
from unittest.mock import patch
from kuristo.__main__ import main


ASSETS_DIR = Path(__file__).parent / "assets"


def test_kuristo_list(capsys):
    test_argv = ["kuristo", "--no-ansi", "list", str(ASSETS_DIR)]
    with patch.object(sys, "argv", test_argv):
        main()

    captured = capsys.readouterr()
    match = re.search(r"Found jobs: (\d+)", captured.out)
    assert match is not None, "Output does not contain 'Found jobs: N'"
    num_jobs = int(match.group(1))
    assert num_jobs > 0, f"Expected more than 0 jobs, got {num_jobs}"
