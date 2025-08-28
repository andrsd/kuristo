from kuristo.registry import action
from kuristo.actions.process_action import ProcessAction
from kuristo.context import Context
from kuristo.utils import interpolate_str
import kuristo.config as config


@action("core/mpi-run")
class MPIAction(ProcessAction):
    """
    Class for running MPI commands
    """

    def __init__(self, name, context: Context, **kwargs) -> None:
        super().__init__(
            name=name,
            context=context,
            **kwargs,
        )
        self._commands = kwargs.get("run", "")
        self._n_ranks = kwargs.get("num-procs", 1)

    @property
    def num_cores(self):
        return self._n_ranks

    def create_sub_command(self) -> str:
        if self.context is None:
            cmds = self._commands
        else:
            cmds = interpolate_str(
                self._commands,
                self.context.vars
            )
        return cmds

    def create_command(self):
        cfg = config.get()
        launcher = cfg.mpi_launcher
        cmd = self.create_sub_command()
        return f'{launcher} -np {self._n_ranks} {cmd}'
