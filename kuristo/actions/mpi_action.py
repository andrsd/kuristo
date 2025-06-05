from ._step import Step


class MPIAction(Step):
    """
    Run an MPI command
    """

    def __init__(self, name, cwd, **kwargs) -> None:
        super().__init__(name, cwd)
        self._n_ranks = kwargs.get("n_procs", 1)

    @property
    def num_cores(self):
        return self._n_ranks

    def _create_command(self) -> str:
        command = f'mpirun -np {self._n_ranks} echo A'
        return command
