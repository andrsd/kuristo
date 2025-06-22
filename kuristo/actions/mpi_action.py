from .._step import Step
from ..context import Context
from abc import abstractmethod


class MPIAction(Step):
    """
    Base class for running MPI commands
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

    @abstractmethod
    def _create_sub_command(self) -> str | None:
        pass

    def _create_command(self):
        launcher = self.context.config.mpi_launcher
        cmd = self._create_sub_command()
        return f'{launcher} -np {self._n_ranks} {cmd}'
