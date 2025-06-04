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
        # return subprocess.Popen(["echo", "seq"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return subprocess.Popen('echo "seq"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
