from kuristo.actions.action import Action
from kuristo.context import Context
from io import StringIO
import contextlib as ctxlib
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

    def run(self) -> int:
        stdout = StringIO()
        stderr = StringIO()

        try:
            with ctxlib.redirect_stdout(stdout), ctxlib.redirect_stderr(stderr):
                self.execute()

            self._stdout = stdout.getvalue().encode()
            self._stderr = stderr.getvalue().encode()
            return 0

        except Exception as e:
            self._stdout = b""
            self._stderr = str(e).encode()
            return 1

    @abstractmethod
    def execute(self) -> None:
        """
        Subclasses must override this method to execute their commands
        """
        pass
