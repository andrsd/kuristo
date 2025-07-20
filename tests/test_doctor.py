import sys
from unittest.mock import patch
from kuristo.__main__ import main


def test_kuristo_doctor(capsys):
    test_argv = ["kuristo", "--no-ansi", "doctor"]
    with patch.object(sys, "argv", test_argv):
        main()

    captured = capsys.readouterr()
    assert len(captured.out) > 0
    assert "Kuristo Diagnostic Report" in captured.out
