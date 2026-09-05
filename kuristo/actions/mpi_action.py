import shlex

import kuristo.config as config
from kuristo.actions.process_action import ProcessAction
from kuristo.context import Context
from kuristo.registry import action


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
        return self._commands

    def create_command(self):
        cfg = config.get()
        cmd = [cfg.mpi_launcher, "-np", f"{self._n_ranks}"]
        sub_cmd = self.create_sub_command()
        if isinstance(sub_cmd, str):
            cmd += shlex.split(sub_cmd)
        else:
            cmd += sub_cmd
        return cmd
