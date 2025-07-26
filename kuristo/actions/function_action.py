from kuristo.actions.action import Action
from kuristo.context import Context
from io import StringIO
import contextlib
from abc import abstractmethod


class FunctionAction(Action):
    """
    Abstract class for defining user action that executes code
    """

    def __init__(self, name, context: Context, **params):
        super().__init__(
            name,
            context,
            **params
        )
        self._params = params

    def run(self, context=None):
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                self.execute()

            self._stdout = stdout_capture.getvalue().encode()
            self._stderr = stderr_capture.getvalue().encode()
            self._return_code = 0

        except Exception as e:
            self._stdout = b""
            self._stderr = str(e).encode()
            self._return_code = 1

    @abstractmethod
    def execute(self) -> None:
        """
        Subclasses must override this method to execute their commands
        """
        pass
