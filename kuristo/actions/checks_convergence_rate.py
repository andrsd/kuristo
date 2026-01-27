import math

import h5py
import numpy as np

from kuristo.actions.action import Action
from kuristo.registry import action


@action("checks/convergence-rate")
class ConvergenceRateCheck(Action):
    def __init__(self, name, context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._input_file = kwargs.get("input")
        self._x_axis_dataset = kwargs.get("x-axis")
        self._y_axis_dataset = kwargs.get("y-axis")
        self._expected_order = float(kwargs.get("expected-order"))
        self._rel_tol = float(kwargs.get("rel-tol", 1e-8))
        self._abs_tol = float(kwargs.get("abs-tol", 0.0))

    def run(self) -> int:
        try:
            with h5py.File(self._input_file, "r") as f:
                dof = f[self._x_axis_dataset]
                err = f[self._y_axis_dataset]
                logN = np.log10(dof)
                logE = np.log10(err)
                # slope b, intercept a
                b, a = np.polyfit(logN, logE, 1)
                value = -b
                if math.isclose(
                    value,
                    self._expected_order,
                    rel_tol=self._rel_tol,
                    abs_tol=self._abs_tol,
                ):
                    self.output = f"Convergence order check passed: got {value}, expected {self._expected_order}"
                    return 0
                else:
                    self.output = (
                        f"Convergence order check failed: got {value}, expected {self._expected_order}, "
                        f"rel-tol={self._rel_tol}, abs-tol={self._abs_tol}"
                    )
                    return -1
        except FileNotFoundError:
            self.output = f"Failed to open {self._input_file}"
            return 0
