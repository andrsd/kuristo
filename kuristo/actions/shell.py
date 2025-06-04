from ._step import Step
import subprocess


class ShellAction(Step):
    """
    This action will run shell command(s)
    """

    def __init__(self, name, commands) -> None:
        super().__init__(name)
        self._commands = commands

    def _create_process(self) -> subprocess.Popen:
        return subprocess.Popen(self._commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
