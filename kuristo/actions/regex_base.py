import re
from abc import abstractmethod
from kuristo.actions.action import Action
from kuristo.utils import interpolate_str


class RegexBaseAction(Action):

    def __init__(self, name, context, pattern, **kwargs):
        super().__init__(name, context, **kwargs)
        self._target_step = kwargs.get("input")
        self._pattern = pattern

    def run(self) -> int:
        output = self._resolve_output()
        matches = re.search(self._pattern, output)
        if matches:
            exit_code = self.on_success(matches)
        else:
            self.on_failure()
            exit_code = -1
        return exit_code

    def _resolve_output(self):
        return interpolate_str(self._target_step, self.context.vars)

    @abstractmethod
    def on_success(self, match) -> int:
        """
        This is called when regex match is sucessful.
        Return a number indicating success: 0 for success, non-zero for failure
        """
        pass

    @abstractmethod
    def on_failure(self):
        """
        This is called when regex match fails
        """
        pass
