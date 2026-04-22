from unittest.mock import MagicMock

from kuristo.actions.shell_action import ShellAction
from kuristo.context import Context


def make_context(vars_dict=None):
    ctx = MagicMock(spec=Context)
    ctx.vars = vars_dict or {}
    return ctx


def test_create_command_returns_preinterpolated_value():
    ctx = make_context({"name": "world"})
    # Command is already interpolated by ActionFactory before being passed to ShellAction
    action = ShellAction("test", ctx, commands="echo world")
    result = action.create_command()
    assert result == "echo world"


def test_create_command_with_list_commands():
    # ShellAction can receive either string or list commands
    ctx = make_context({})
    cmd_list = ["echo", "hello", "world"]
    action = ShellAction("test", ctx, commands=cmd_list)
    result = action.create_command()
    assert result == cmd_list


def test_create_command_no_context_raises():
    action = ShellAction("test", None, commands="echo hi")
    result = action.create_command()
    assert "echo hi" in result
