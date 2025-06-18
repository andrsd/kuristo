from .._step import Step


class ShellAction(Step):
    """
    This action will run shell command(s)
    """

    def __init__(self, name, cwd, commands) -> None:
        super().__init__(name, cwd)
        self._commands = commands

    def _create_command(self) -> str:
        return self._commands
