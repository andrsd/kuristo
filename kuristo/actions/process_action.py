from kuristo.actions.action import Action
from kuristo.context import Context
import os
import subprocess
from abc import abstractmethod


class ProcessAction(Action):
    """
    Base class for job step
    """

    def __init__(self, name, context: Context, **kwargs) -> None:
        super().__init__(name, context, **kwargs)
        self._process = None
        self._env = kwargs.get('env', {})

    @property
    def command(self) -> str:
        """
        Return command
        """
        return self.create_command()

    def run(self) -> int:
        timeout = self.timeout_minutes
        env = os.environ.copy()
        if self.context is not None:
            env.update(self.context.env)
        env.update((var, str(val)) for var, val in self._env.items())
        self._process = subprocess.Popen(
            self.command,
            shell=True,
            cwd=self._cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        try:
            stdout, _ = self._process.communicate(
                timeout=timeout * 60
            )
            if self.id is not None:
                self.context.vars["steps"][self.id] = {
                    "output": stdout.decode()
                }
            self.output = stdout
            return self._process.returncode

        except subprocess.TimeoutExpired:
            self.terminate()
            outs, _ = self._process.communicate()
            outs += b'\n'
            outs += 'Step timed out'.encode()
            self.output = outs
            return 124
        except subprocess.SubprocessError:
            self.output = b''
            return -1

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
