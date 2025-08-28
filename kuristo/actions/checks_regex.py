import re
from kuristo.registry import action
from kuristo.actions.regex_base import RegexBaseAction

ALIAS_PATTERNS = {
    "float": r"([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)",
    "int": r"([-+]?\d+)",
}

ALIAS_RE = re.compile(r"{:(\w+):}")


@action("checks/regex")
class RegexCheck(RegexBaseAction):

    def __init__(self, name, context, **kwargs):
        pattern = kwargs.pop("pattern", [])
        super().__init__(
            name,
            context,
            pattern=self._expand_pattern(pattern),
            **kwargs)

    def on_success(self, match) -> int:
        self.output = "Regex check passed."
        return 0

    def on_failure(self):
        self.output = "Regex check failed"

    def _expand_pattern(self, pattern: str) -> str:
        def replacer(match):
            name = match.group(1)
            # fallback to original if not found
            return ALIAS_PATTERNS.get(name, match.group(0))

        return ALIAS_RE.sub(replacer, pattern)
