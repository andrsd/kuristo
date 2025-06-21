from .._step import Step
from ..context import Context
from kuristo import action


@action("core/mpi")
class MPIAction(Step):
    """
    Run an MPI command
    """

    def __init__(self, name, context: Context, **kwargs) -> None:
        super().__init__(
            name=name,
            context=context,
            **kwargs,
        )
        self._n_ranks = kwargs.get("n_procs", 1)

    @property
    def num_cores(self):
        return self._n_ranks

    def _create_command(self):
        command = f'mpirun -np {self._n_ranks} echo A'
        return command
