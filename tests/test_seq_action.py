from kuristo.actions.seq_action import SeqAction
from kuristo.context import Context
from unittest.mock import MagicMock
import kuristo.registry as registry


def make_context():
    return MagicMock(spec=Context)


def test_default_num_cores():
    ctx = make_context()
    action = SeqAction(name="test_seq", context=ctx)
    assert action.num_cores == 1  # default value


def test_custom_num_cores():
    ctx = make_context()
    action = SeqAction(name="test_seq", context=ctx, **{'num-cores': 4})
    assert action.num_cores == 4


def test_create_command_returns_echo_seq():
    ctx = make_context()
    action = SeqAction(name="test_seq", context=ctx)
    assert action.create_command() == "echo seq"


def test_action_is_registered():
    assert registry.get_action("core/sequential") is SeqAction
