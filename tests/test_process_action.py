import subprocess
import pytest
from unittest.mock import MagicMock, patch
from kuristo.actions.process_action import ProcessAction


# Minimal context stub
class DummyContext:
    def __init__(self):
        self.env = {}
        self.vars = {"steps": {}}


# Minimal concrete subclass for testing
class TrivialProcessAction(ProcessAction):
    def create_command(self) -> str:
        return "echo test"


@pytest.fixture
def action_instance():
    return TrivialProcessAction("test", DummyContext())


def test_successful_run(action_instance):
    mock_popen = MagicMock()
    mock_popen.communicate.return_value = (b"output", None)
    mock_popen.returncode = 0
    with patch("subprocess.Popen", return_value=mock_popen):
        exit_code = action_instance.run()
        assert exit_code == 0
    assert action_instance.output == "output"


def test_timeout_handling(action_instance):
    mock_popen = MagicMock()
    # First call raises TimeoutExpired, second call returns bytes
    mock_popen.communicate.side_effect = [
        subprocess.TimeoutExpired(cmd="cmd", timeout=1),
        (b"", b""),
    ]
    with patch("subprocess.Popen", return_value=mock_popen):
        exit_code = action_instance.run()
        assert exit_code == 124
    assert action_instance.output.endswith("Step timed out")


def test_subprocess_error_handling(action_instance):
    mock_popen = MagicMock()
    mock_popen.communicate.side_effect = subprocess.SubprocessError()
    with patch("subprocess.Popen", return_value=mock_popen):
        exit_code = action_instance.run()
        assert exit_code == -1
    assert action_instance.output == ""


def test_terminate_kills_process(action_instance):
    mock_process = MagicMock()
    action_instance._process = mock_process
    action_instance.terminate()
    mock_process.kill.assert_called_once()
