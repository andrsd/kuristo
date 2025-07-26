from .process_action import ProcessAction
from kuristo.utils import interpolate_str
from ..context import Context


class ShellAction(ProcessAction):
    """
    This action will run shell command(s)
    """

    def __init__(self, name, context: Context, commands, **kwargs) -> None:
        super().__init__(name, context, **kwargs)
        self._commands = commands

    def create_command(self):
        assert self.context is not None
        cmds = interpolate_str(
            self._commands,
            self.context.vars
        )
        return cmds
