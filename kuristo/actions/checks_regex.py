import re
from kuristo.registry import action
from kuristo.actions.action import Action
from kuristo.utils import interpolate_str

ALIAS_PATTERNS = {
    "float": r"([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)",
    "int": r"([-+]?\d+)",
}

ALIAS_RE = re.compile(r"{:(\w+):}")


@action("checks/regex")
class RegexCheck(Action):

    def __init__(self, name, context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._target_step = kwargs["input"]
        self._pattern = self._expand_pattern(kwargs.get("pattern", []))

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

    def _expand_pattern(self, pattern: str) -> str:
        def replacer(match):
            name = match.group(1)
            # fallback to original if not found
            return ALIAS_PATTERNS.get(name, match.group(0))

        return ALIAS_RE.sub(replacer, pattern)
