import subprocess
from abc import ABC, abstractmethod
import os
from .context import Context


class Step(ABC):
    """
    Base class for job step
    """

    def __init__(self, name, context: Context, **kwargs) -> None:
        self._cwd = kwargs.get("working_dir", None)
        self._id = kwargs.get("id", None)
        self._process = None
        self._stdout = None
        self._stderr = None
        self._return_code = -1
        if name is None:
            self._name = ""
        else:
            self._name = name
        self._context = context
        self._timeout_minutes = kwargs.get("timeout_minutes", 60)

    @property
    def name(self):
        """
        Return step name
        """
        return self._name

    @property
    def id(self):
        """
        Return step ID
        """
        return self._id

    @property
    def command(self):
        """
        Return command
        """
        return self._create_command()

    @property
    def return_code(self) -> int:
        """
        Return code of the step
        """
        return self._return_code

    @property
    def num_cores(self) -> int:
        return 1

    @property
    def stdout(self):
        """
        Return stdout of the jobs
        """
        if self._stdout:
            return self._stdout
        else:
            return b''

    @property
    def timeout_minutes(self):
        """
        Return timeout in minutes
        """
        return self._timeout_minutes

    @property
    def context(self):
        """
        Return context
        """
        return self._context

    def run(self, context=None):
        timeout = self.timeout_minutes
        env = os.environ.copy()
        if context is not None:
            env.update(context.env)
        self._process = subprocess.Popen(
            self.command,
            shell=True,
            cwd=self._cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            self._stdout, self._stderr = self._process.communicate(
                timeout=timeout * 60
            )
            self._return_code = self._process.returncode
            if self.id is not None:
                self.context.vars["steps"][self.id] = {
                    "output": self._stdout.decode()
                }

        except subprocess.TimeoutExpired:
            self.terminate()
            outs, errs = self._process.communicate()
            self._stdout = None
            self._stderr = 'Step timed out'.encode()
            self._return_code = 124
        except:
            self._stdout = None
            self._stderr = b''
            self._return_code = -1

    def terminate(self):
        if self._process is not None:
            self._process.kill()

    @abstractmethod
    def _create_command(self) -> str | None:
        pass
