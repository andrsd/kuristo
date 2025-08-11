from kuristo.actions.process_action import ProcessAction
from kuristo.context import Context
import kuristo.config as config
from abc import abstractmethod


class MPIAction(ProcessAction):
    """
    Base class for running MPI commands
    """

    def __init__(self, name, context: Context, **kwargs) -> None:
        super().__init__(
            name=name,
            context=context,
            **kwargs,
        )
        self._n_ranks = kwargs.get("n-procs", 1)

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
        cfg = config.get()
        launcher = cfg.mpi_launcher
        cmd = self.create_sub_command()
        return f'{launcher} -np {self._n_ranks} {cmd}'
