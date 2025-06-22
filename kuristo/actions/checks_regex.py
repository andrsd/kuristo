import re
from kuristo import action
from .step import Step
from .._utils import interpolate_str


@action("checks/regex")
class RegexCheck(Step):
    def __init__(self, name, context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._target_step = kwargs["input"]
        self._pattern = kwargs.get("pattern", [])

    def run(self, context=None):
        output = self._resolve_output()
        matches = re.search(self._pattern, output)
        if matches:
            self._output = "Regex check passed."
            self._return_code = 0
        else:
            self._output = "Regex check failed"
            self._return_code = -1
        self._output = self._output.encode()

    def _resolve_output(self):
        return interpolate_str(self._target_step, self.context.vars)
