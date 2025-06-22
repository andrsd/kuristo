from abc import ABC, abstractmethod
from ..context import Context


class Step(ABC):
    """
    Base class for job step
    """

    def __init__(self, name, context: Context, **kwargs) -> None:
        self._cwd = kwargs.get("working_dir", None)
        self._id = kwargs.get("id", None)
        self._return_code = -1
        if name is None:
            self._name = ""
        else:
            self._name = name
        self._output = None
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
    def return_code(self) -> int:
        """
        Return code of the step
        """
        return self._return_code

    @property
    def num_cores(self) -> int:
        return 1

    @property
    def output(self):
        """
        Return output of the jobs
        """
        if self._output:
            return self._output
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

    @abstractmethod
    def run(self, context=None):
        pass
