from ._step import Step
import subprocess


class SeqAction(Step):
    """
    Run a sequential command
    """

    def __init__(self, name, **kwargs) -> None:
        super().__init__(name)
        self._n_cores = kwargs.get("n_cores", 1)

    @property
    def num_cores(self):
        return self._n_cores

    def _create_process(self) -> subprocess.Popen:
        cmd = ["echo", "seq"]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
