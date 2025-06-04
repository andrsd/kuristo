from ._step import Step
import subprocess


class MPIAction(Step):
    """
    Run an MPI command
    """

    def __init__(self, name, **kwargs) -> None:
        super().__init__(name)
        self._n_ranks = kwargs.get("n_procs", 1)

    @property
    def num_cores(self):
        return self._n_ranks

    def _create_process(self) -> subprocess.Popen:
        # cmd = ["mpirun", "-np", self._n_ranks, "echo", "\"seq\""]
        # return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return subprocess.Popen("echo", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
