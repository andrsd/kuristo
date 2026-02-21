import shlex
import subprocess
import os
from kuristo.registry import action
from kuristo.actions.process_action import ProcessAction
from kuristo.context import Context


@action("checks/h5diff")
class H5DiffCheck(ProcessAction):
    """
    Run h5diff on two HDF5 files, optionally comparing specific datasets.

    Parameters:
        gold (str): Path to gold/reference file
        test (str): Path to test output file
        rel-tol (float): Relative tolerance (used if no datasets specified)
        abs-tol (float): Absolute tolerance (used if no datasets specified)
        fail-on-diff (bool): If false, ignore diff return code
        datasets (list, optional): List of datasets to compare with individual tolerances.
                                 Each item is a dict with 'path', and optionally 'rel-tol'/'abs-tol'
    """

    def __init__(self, name, context: Context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._gold_path = kwargs["gold"]
        self._test_path = kwargs["test"]
        self._fail_on_diff = kwargs.get("fail-on-diff", True)

        # Check if comparing specific datasets or entire files
        self._datasets = kwargs.get("datasets", None)

        if self._datasets:
            # Multiple datasets mode - validate each dataset
            if not isinstance(self._datasets, list):
                raise RuntimeError("h5diff: `datasets` must be a list")
            self._validate_datasets()
        else:
            # Single file comparison mode (backward compatible)
            self._rel_tol = kwargs.get("rel-tol", None)
            self._abs_tol = kwargs.get("abs-tol", None)
            if self._rel_tol is None and self._abs_tol is None:
                raise RuntimeError("h5diff: Must provide either `rel-tol` or `abs-tol`")

    def _validate_datasets(self):
        """Validate that each dataset has required tolerance"""
        for i, dataset in enumerate(self._datasets):
            if not isinstance(dataset, dict):
                raise RuntimeError(
                    f"h5diff: dataset[{i}] must be a dictionary with 'path' and tolerance"
                )
            if "path" not in dataset:
                raise RuntimeError(f"h5diff: dataset[{i}] must have a 'path' field")
            rel_tol = dataset.get("rel-tol", None)
            abs_tol = dataset.get("abs-tol", None)
            if rel_tol is None and abs_tol is None:
                raise RuntimeError(
                    f"h5diff: dataset[{i}] ({dataset['path']}) must provide either `rel-tol` or `abs-tol`"
                )

    def _create_command_for_dataset(self, dataset: dict) -> str:
        """Create h5diff command for a single dataset"""
        cmd = ["h5diff"]
        cmd += ["-r"]

        abs_tol = dataset.get("abs-tol", None)
        rel_tol = dataset.get("rel-tol", None)

        if abs_tol is not None:
            cmd += [f"--delta={abs_tol}"]
        elif rel_tol is not None:
            cmd += [f"--relative={rel_tol}"]

        cmd += [self._gold_path]
        cmd += [self._test_path]
        cmd += [dataset["path"]]

        return shlex.join(cmd)

    def create_command(self):
        """Create command for backward compatibility (single file comparison)"""
        if self._datasets:
            # For multiple datasets, we can't return a single command
            # This is handled in run() instead
            return ""

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
        """Run h5diff comparison(s)"""
        if self._datasets:
            # Multiple datasets mode
            return self._run_multiple_datasets()
        else:
            # Single file comparison mode (backward compatible)
            return self._run_single_file()

    def _run_single_file(self) -> int:
        """Run comparison of entire files (original behavior)"""
        exit_code = super().run()

        # interpret return code
        if exit_code != 0:
            if self._fail_on_diff:
                return exit_code
            else:
                # Allow diffs (dev mode), override return code
                return 0
        else:
            return 0

    def _run_multiple_datasets(self) -> int:
        """Run h5diff for each dataset and aggregate results"""
        timeout = self.timeout_minutes
        env = os.environ.copy()
        if self.context is not None:
            env.update(self.context.env)
        env.update((var, str(val)) for var, val in self._env.items())

        all_passed = True
        outputs = []

        for dataset in self._datasets:
            cmd = self._create_command_for_dataset(dataset)
            dataset_path = dataset["path"]

            try:
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=self._cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )

                stdout, _ = process.communicate(timeout=timeout * 60)
                output = stdout.decode()
                outputs.append(
                    f"Dataset {dataset_path}: exit code {process.returncode}\n{output}"
                )

                if process.returncode != 0:
                    all_passed = False

            except subprocess.TimeoutExpired:
                process.kill()
                all_passed = False
                outputs.append(f"Dataset {dataset_path}: TIMEOUT")

        # Store combined output
        if self.id is not None:
            combined_output = "\n".join(outputs)
            self.context.vars["steps"][self.id] = {"output": combined_output}

        self.output = "\n".join(outputs).encode()

        # Return appropriate exit code
        if all_passed:
            return 0
        elif self._fail_on_diff:
            return 1
        else:
            return 0
