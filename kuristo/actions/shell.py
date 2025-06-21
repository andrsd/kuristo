from .._step import Step
from .._utils import interpolate_str
from ..context import Context


class ShellAction(Step):
    """
    This action will run shell command(s)
    """

    def __init__(self, name, cwd, timeout, context: Context, commands) -> None:
        super().__init__(
            name=name,
            cwd=cwd,
            timeout=timeout,
            context=context
        )
        self._commands = commands

    def _create_command(self):
        assert(self.context is not None)
        cmds = interpolate_str(
            self._commands,
            self.context.vars
        )
        return cmds
