import os
import shlex

from kuristo.actions.process_action import ProcessAction
from kuristo.context import Context
from kuristo.registry import action
from kuristo.utils import resolve_path


@action("checks/exodiff")
class ExodiffCheck(ProcessAction):
    """
    Run exodiff on two Exodus files.

    Parameters:
        reference (str): Path to gold/reference file (can be prefixed with source: or build:)
        test (str): Path to test output file (same rules apply)
        rel-tol (float): Relative tolerance
        abs-tol (float): Absolute tolerance
        floor (float): Floor tolerance
        extra_args (list[str]): Raw args passed to exodiff
        fail_on_diff (bool): If false, ignore diff return code
    """

    def __init__(
        self,
        name,
        context: Context,
        id,
        working_dir,
        timeout_minutes,
        reference=None,
        test=None,
        floor=None,
        extra_args=None,
        source_root=None,
        build_root=None,
        fail_on_diff=True,
        **kwargs,
    ):
        super().__init__(
            name=name,
            context=context,
            working_dir=working_dir,
            timeout_minutes=timeout_minutes,
            **kwargs,
        )
        self._source_root = source_root or os.getcwd()
        self._build_root = build_root or os.getcwd()

        self._ref_path = resolve_path(
            path_str=reference,
            build_root=self._build_root,
            source_root=self._source_root,
        )
        self._test_path = resolve_path(
            path_str=test, build_root=self._build_root, source_root=self._source_root
        )
        self._abs_tol = kwargs.get("abs-tol", None)
        self._rel_tol = kwargs.get("rel-tol", None)
        self._floor = floor
        self._extra_args = extra_args or []
        self._fail_on_diff = fail_on_diff

    def create_command(self):
        cmd = ["exodiff"]

        if self._abs_tol is not None:
            cmd += ["-tolerance", str(self._abs_tol)]
            cmd += ["-absolute"]
        if self._rel_tol is not None:
            cmd += ["-tolerance", str(self._rel_tol)]
            cmd += ["-absolute"]

        if self._floor is not None:
            cmd += ["-Floor", str(self._floor)]

        cmd += self._extra_args
        cmd += [self._ref_path, self._test_path]

        return shlex.join(cmd)

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
