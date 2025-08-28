from kuristo.actions.process_action import ProcessAction
from kuristo.utils import interpolate_str
from kuristo.context import Context


class ShellAction(ProcessAction):
    """
    This action will run shell command(s)
    """

    def __init__(self, name, context: Context, commands, **kwargs) -> None:
        super().__init__(name, context, **kwargs)
        self._commands = commands
        self._n_cores = kwargs.get("num_cores", 1)

    def create_command(self):
        if self.context is None:
            cmds = self._commands
        else:
            cmds = interpolate_str(
                self._commands,
                self.context.vars
            )
        return cmds

    @property
    def num_cores(self):
        return self._n_cores
