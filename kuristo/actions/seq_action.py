from ._step import Step


class SeqAction(Step):
    """
    Run a sequential command
    """

    def __init__(self, name, cwd, **kwargs) -> None:
        super().__init__(name, cwd)
        self._n_cores = kwargs.get("n_cores", 1)

    @property
    def num_cores(self):
        return self._n_cores

    def _create_command(self) -> str:
        command = f'echo seq'
        return command
