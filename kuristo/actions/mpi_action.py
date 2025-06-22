from .process_step import ProcessStep
from ..context import Context
from abc import abstractmethod


class MPIAction(ProcessStep):
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
    def create_sub_command(self) -> str:
        """
        Subclasses must override this method to return the shell command that will be
        executed by the MPI launcher
        """
        pass

    def create_command(self):
        launcher = self.context.config.mpi_launcher
        cmd = self.create_sub_command()
        return f'{launcher} -np {self._n_ranks} {cmd}'
