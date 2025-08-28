from kuristo.actions.checks_regex import RegexCheck
from kuristo.registry import action
import math


@action("checks/regex-float")
class RegexFloatCheck(RegexCheck):
    def __init__(self, name, context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._gold = float(kwargs["gold"])
        self._rel_tol = float(kwargs.get("rel-tol", 1e-8))
        self._abs_tol = float(kwargs.get("abs-tol", 0.0))

    def on_success(self, match) -> int:
        try:
            value = float(match.group(1))
            if math.isclose(value, self._gold, rel_tol=self._rel_tol, abs_tol=self._abs_tol):
                self.output = (
                    f"Regex float check passed: got {value}, expected {self._gold}"
                )
                return 0
            else:
                self.output = (
                    f"Regex float check failed: got {value}, expected {self._gold}, "
                    f"rel-tol={self._rel_tol}, abs-tol={self._abs_tol}"
                )
                return -1
        except ValueError:
            self.output = (
                f"Regex matched value '{match.group(1)}' but it is not a float."
            )
            return -1

    def on_failure(self):
        self.output = f"Pattern '{self.pattern}' not found in output"
