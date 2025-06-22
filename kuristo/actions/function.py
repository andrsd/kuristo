from ..registry import get_step
from .step import Step
from ..context import Context
from io import StringIO
import contextlib


class FunctionStep(Step):
    def __init__(self, name, context: Context, func_name, **params):
        super().__init__(
            name,
            context,
            **params
        )
        self._func_name = func_name
        self._params = params

    def run(self, context=None):
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            func = get_step(self._func_name)

            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                func(self._params)

            self._stdout = stdout_capture.getvalue().encode()
            self._stderr = stderr_capture.getvalue().encode()
            self._return_code = 0

        except Exception as e:
            self._stdout = b""
            self._stderr = str(e).encode()
            self._return_code = 1
