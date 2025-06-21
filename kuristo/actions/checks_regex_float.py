from .checks_regex import RegexCheck
from kuristo import action
import re
import math


@action("checks/regex-float")
class RegexFloatCheck(RegexCheck):
    def __init__(self, name, context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._gold = float(kwargs["gold"])
        self._rel_tol = float(kwargs.get("rel_tol", 1e-8))
        self._abs_tol = float(kwargs.get("abs_tol", 0.0))

    def run(self, context=None):
        output = self._resolve_output()
        match = re.search(self._pattern, output)
        if not match:
            self._stdout = f"Pattern '{self._pattern}' not found in output"
            self._return_code = -1
        else:
            try:
                value = float(match.group(1))
                if math.isclose(value, self._gold, rel_tol=self._rel_tol, abs_tol=self._abs_tol):
                    self._stdout = (
                        f"Regex float check passed: got {value}, expected {self._gold}"
                    )
                    self._return_code = 0
                else:
                    self._stdout = (
                        f"Regex float check failed: got {value}, expected {self._gold}, "
                        f"rel_tol={self._rel_tol}, abs_tol={self._abs_tol}"
                    )
                    self._return_code = -1
            except ValueError:
                self._stdout = (
                    f"Regex matched value '{match.group(1)}' but it is not a float."
                )
                self._return_code = -1

        self._stdout = self._stdout.encode()
