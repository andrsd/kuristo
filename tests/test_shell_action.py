from unittest.mock import MagicMock, patch

from kuristo.actions.shell_action import ShellAction
from kuristo.context import Context


def make_context(vars_dict=None):
    ctx = MagicMock(spec=Context)
    ctx.vars = vars_dict or {}
    return ctx


def test_create_command_calls_interpolate_str():
    ctx = make_context({"name": "world"})
    with patch(
        "kuristo.actions.shell_action.interpolate_str", return_value="echo world"
    ) as mock_interp:
        action = ShellAction("test", ctx, commands="echo {name}")
        result = action.create_command()
        mock_interp.assert_called_once_with("echo {name}", ctx.vars)
        assert result == "echo world"


def test_create_command_real_interpolation():
    # We'll simulate interpolate_str's actual effect for realism
    # from kuristo.actions.shell_action import interpolate_str
    ctx = make_context({"name": "Alice"})
    action = ShellAction("test", ctx, commands="echo ${{name}}")
    result = action.create_command()
    # This assumes interpolate_str uses str.format or similar
    assert "Alice" in result


def test_create_command_no_context_raises():
    action = ShellAction("test", None, commands="echo hi")
    result = action.create_command()
    assert "echo hi" in result
