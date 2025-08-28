from abc import ABC, abstractmethod
from kuristo.context import Context


class Action(ABC):
    """
    Base class for job action
    """

    def __init__(self, name, context: Context, **kwargs) -> None:
        self._cwd = kwargs.get("working_dir", None)
        self._id = kwargs.get("id", None)
        if name is None:
            self._name = ""
        else:
            self._name = name
        self._output = None
        self._context = context
        self._timeout_minutes = kwargs.get("timeout_minutes", 60)
        self._continue_on_error = kwargs.get("continue_on_error", False)

    @property
    def name(self):
        """
        Return action name
        """
        return self._name

    @property
    def id(self):
        """
        Return action ID
        """
        return self._id

    @property
    def num_cores(self) -> int:
        return 1

    @property
    def output(self):
        """
        Return output of the action
        """
        if self._output:
            return self._output
        else:
            return b''

    @output.setter
    def output(self, str):
        self._output = str

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

    @property
    def continue_on_error(self):
        return self._continue_on_error

    @abstractmethod
    def run(self) -> int:
        pass
