import math

import h5py
import numpy as np

from kuristo.actions.action import Action
from kuristo.registry import action
from kuristo.utils import scalar_or_list


def to_array(data, n_comps, name: str):
    """
    Converts `data` into an array. If data is a single value and `n_comps` is
    larger than 1, then this return and array with `data` repeated `n_comps`
    times. If `data` has `n_comps`, then this returns `data` as an array of
    floats.
    """
    array = np.asarray(data)
    if array.ndim == 0:
        return np.full(n_comps, float(array))
    elif array.ndim == 1 and array.size == n_comps:
        return array.astype(float)
    else:
        raise ValueError(f"{name} must be scalar or length {n_comps}, got {data}")


@action("checks/convergence-rate")
class ConvergenceRateCheck(Action):
    def __init__(self, name, context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._input_file = kwargs.get("input")
        self._x_axis_dataset = kwargs.get("x-axis")
        self._y_axis_dataset = kwargs.get("y-axis")
        self._expected_order = scalar_or_list(kwargs, "expected-order")
        self._abs_tol = scalar_or_list(kwargs, "abs-tol")

    def run(self) -> int:
        try:
            with h5py.File(self._input_file, "r") as f:
                dof = np.asarray(f[self._x_axis_dataset])
                err = np.asarray(f[self._y_axis_dataset])

            logN = np.log10(dof)
            if err.ndim == 1:
                err = err[:, None]
            elif err.ndim == 2:
                # If stored as (ncomp, N), transpose
                if err.shape[0] != logN.shape[0] and err.shape[1] == logN.shape[0]:
                    err = err.T
            else:
                raise ValueError("y-axis dataset must be 1D or 2D")

            ncomp = err.shape[1]
            logE = np.log10(err)
            expected = to_array(self._expected_order, ncomp, "expected-order")
            abs_tol = to_array(self._abs_tol, ncomp, "abs-tol")
            values = []
            passed = True
            for i in range(logE.shape[1]):
                # slope b, intercept a
                b, a = np.polyfit(logN, logE[:, i], 1)
                value = float(-b)
                values.append(value)

                if not math.isclose(
                    value,
                    expected[i],
                    abs_tol=abs_tol[i],
                ):
                    passed = False

            if passed:
                self.output = f"Convergence order check passed: got {str(values)}, expected {expected.tolist()}"
                return 0
            else:
                self.output = (
                    f"Convergence order check failed: got {values}, expected {expected.tolist()}, "
                    f"abs-tol={self._abs_tol}"
                )
                return -1
        except FileNotFoundError:
            self.output = f"Failed to open {self._input_file}"
            return 0
