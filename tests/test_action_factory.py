import pytest
from unittest.mock import MagicMock, patch
from kuristo.action_factory import ActionFactory


class DummyStep:
    def __init__(
        self,
        name="test",
        id="step1",
        working_directory="/tmp",
        timeout_minutes=5,
        continue_on_error=False,
        num_cores=1,
        run=None,
        uses=None,
        params=None
    ):
        self.name = name
        self.id = id
        self.working_directory = working_directory
        self.timeout_minutes = timeout_minutes
        self.continue_on_error = continue_on_error
        self.num_cores = num_cores
        self.run = run
        self.uses = uses
        self.params = params or {}
        self.env = {}


@pytest.fixture
def dummy_context():
    return MagicMock()


def test_create_shell_action_when_uses_is_none(dummy_context):
    ts = DummyStep(run=["echo", "hello"], uses=None)
    with patch("kuristo.action_factory.ShellAction") as mock_shell:
        result = ActionFactory.create(ts, dummy_context)

    mock_shell.assert_called_once_with(
        ts.name,
        dummy_context,
        id=ts.id,
        working_dir=ts.working_directory,
        timeout_minutes=ts.timeout_minutes,
        continue_on_error=False,
        num_cores=1,
        commands=ts.run,
        env={}
    )
    assert result == mock_shell.return_value


def test_create_registered_action(dummy_context):
    ts = DummyStep(uses="custom.action", params={"foo": "bar"})

    mock_action_cls = MagicMock()
    with patch("kuristo.action_factory.get_action", return_value=mock_action_cls):
        result = ActionFactory.create(ts, dummy_context)

    mock_action_cls.assert_called_once_with(
        ts.name,
        dummy_context,
        id=ts.id,
        working_dir=ts.working_directory,
        timeout_minutes=ts.timeout_minutes,
        continue_on_error=False,
        foo="bar",
    )
    assert result == mock_action_cls.return_value


def test_create_unknown_action_raises(dummy_context):
    ts = DummyStep(uses="unknown.action")
    with patch("kuristo.action_factory.get_action", return_value=None):
        with pytest.raises(RuntimeError) as excinfo:
            ActionFactory.create(ts, dummy_context)
    assert "unknown.action" in str(excinfo.value)
