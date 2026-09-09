from kuristo.actions.process_action import ProcessAction
from kuristo.context import Context
from kuristo.registry import action
from kuristo.utils import resolve_path


@action("checks/exodiff")
class ExodiffCheck(ProcessAction):
    """
    Run exodiff on two Exodus files.

    Parameters:
        gold (str): Path to gold/reference file
        test (str): Path to test output file
        rel-tol (float): Relative tolerance
        abs-tol (float): Absolute tolerance
        floor (float): Floor tolerance
        extra-args (list[str]): Raw args passed to exodiff
        fail-on-diff (bool): If false, ignore diff return code
    """

    def __init__(self, name, context: Context, **kwargs):
        super().__init__(name=name, context=context, **kwargs)

        self._gold_path = resolve_path(kwargs["gold"], self.working_directory)
        self._test_path = resolve_path(kwargs["test"], self.working_directory)
        self._abs_tol = kwargs.get("abs-tol", None)
        self._rel_tol = kwargs.get("rel-tol", None)
        self._floor = kwargs.get("floor", None)
        self._extra_args = kwargs.get("extra-args", [])
        self._fail_on_diff = kwargs.get("fail-on-diff", True)

        if self._abs_tol is not None and self._rel_tol is not None:
            raise Exception(
                "checks/exodiff: Cannot supply both relative and absolute tolerance at the same time"
            )

    def create_command(self):
        cmd = ["exodiff"]

        if self._abs_tol is not None:
            cmd += ["-tolerance", str(self._abs_tol)]
            cmd += ["-absolute"]
        if self._rel_tol is not None:
            cmd += ["-tolerance", str(self._rel_tol)]
            cmd += ["-relative"]

        if self._floor is not None:
            cmd += ["-Floor", str(self._floor)]

        cmd += self._extra_args
        cmd += [self._gold_path, self._test_path]

        return cmd

    def run(self) -> int:
        exit_code = super().run()

        # interpret exodiff return code
        if exit_code != 0:
            if self._fail_on_diff:
                # Leave return_code as is, fail the test
                return exit_code
            else:
                # Allow diffs (dev mode), override return code
                return 0
        else:
            return 0
