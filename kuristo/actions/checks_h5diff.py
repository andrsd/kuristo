import shlex
from kuristo.registry import action
from kuristo.actions.process_action import ProcessAction
from kuristo.context import Context


@action("checks/h5diff")
class H5DiffCheck(ProcessAction):
    """
    Run h5diff on two HDF5 files.

    Parameters:
        gold (str): Path to gold/reference file
        test (str): Path to test output file
        rel-tol (float): Relative tolerance
        abs-tol (float): Absolute tolerance
        fail-on-diff (bool): If false, ignore diff return code
    """

    def __init__(self, name, context: Context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._gold_path = kwargs["gold"]
        self._test_path = kwargs["test"]
        # "global" tolerances
        self._rel_tol = kwargs.get("rel-tol", None)
        self._abs_tol = kwargs.get("abs-tol", None)
        self._fail_on_diff = kwargs.get("fail-on-diff", True)
        if self._rel_tol is None and self._abs_tol is None:
            raise RuntimeError("h5diff: Must provide either `rel-tol` or `abs-tol`")

    def create_command(self):
        cmd = ["h5diff"]
        cmd += ["-r"]
        if self._abs_tol is not None:
            cmd += [f"--delta={self._abs_tol}"]
        elif self._rel_tol is not None:
            cmd += [f"--relative={self._rel_tol}"]
        cmd += [self._gold_path]
        cmd += [self._test_path]
        return shlex.join(cmd)

    def run(self) -> int:
        exit_code = super().run()

        # interpret return code
        if exit_code != 0:
            if self._fail_on_diff:
                # Leave return_code as is, fail the test
                return exit_code
            else:
                # Allow diffs (dev mode), override return code
                return 0
        else:
            return 0
