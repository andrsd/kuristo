import subprocess
from abc import ABC, abstractmethod


class Step(ABC):
    """
    Base class for job step
    """

    def __init__(self, name) -> None:
        self._process = None
        self._stdout = None
        self._stderr = None
        self._return_code = -1
        if name is None:
            self._name = ""
        else:
            self._name = name

    @property
    def name(self):
        """
        Return step name
        """
        return self._name

    @property
    def return_code(self) -> int:
        """
        Return code of the step
        """
        return self._return_code

    @property
    def num_cores(self):
        return 1

    @property
    def stdout(self):
        """
        Return stdout of the jobs
        """
        return self._stdout

    def run(self):
        try:
            self._process = self._create_process()
            self._stdout, self._stderr = self._process.communicate()
            self._return_code = self._process.returncode
        except:
            self._stdout = b''
            self._stderr = b''
            self._return_code = -1

    @abstractmethod
    def _create_process(self) -> subprocess.Popen:
        pass
