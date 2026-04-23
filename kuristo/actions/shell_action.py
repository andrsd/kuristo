from kuristo.actions.process_action import ProcessAction
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
        return self._commands

    @property
    def num_cores(self):
        return self._n_cores
