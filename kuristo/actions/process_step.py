from .step import Step
from ..context import Context
import os
import subprocess
from abc import ABC, abstractmethod


class ProcessStep(Step):
    """
    Base class for job step
    """

    def __init__(self, name, context: Context, **kwargs) -> None:
        super().__init__(name, context, **kwargs)
        self._process = None
        self._stdout = None
        self._stderr = None

    @property
    def command(self) -> str:
        """
        Return command
        """
        return self.create_command()

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
    def stderr(self):
        """
        Return stderr of the jobs
        """
        if self._stderr:
            return self._stderr
        else:
            return b''

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
            self._output = self._stdout

        except subprocess.TimeoutExpired:
            self.terminate()
            outs, errs = self._process.communicate()
            self._stderr = 'Step timed out'.encode()
            self._return_code = 124
        except subprocess.SubprocessError:
            self._stderr = b''
            self._return_code = -1

    def terminate(self):
        if self._process is not None:
            self._process.kill()

    @abstractmethod
    def create_command(self) -> str:
        """
        Subclasses must override this method to return the shell command that will be
        executed by this step.

        @return None if the step does not run a command.
        """
        pass
