from .._step import Step


class ShellAction(Step):
    """
    This action will run shell command(s)
    """

    def __init__(self, name, cwd, timeout, commands) -> None:
        super().__init__(
            name=name,
            cwd=cwd,
            timeout=timeout
        )
        self._commands = commands

    def _create_command(self):
        return self._commands
