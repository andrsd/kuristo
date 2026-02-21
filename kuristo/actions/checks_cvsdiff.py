import csv
import math
from kuristo.registry import action
from kuristo.actions.action import Action


@action("checks/csv-diff")
class CSVDiffCheck(Action):
    def __init__(self, name, context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._gold_path = kwargs["gold"]
        self._test_path = kwargs["test"]
        self._lines = kwargs.get("lines", "all")
        self._columns = kwargs.get("columns", "all")
        self._tolerances = kwargs.get("tolerances", {})

        self._default_rel = float(kwargs.get("rel-tol", 1e-6))
        self._default_abs = float(kwargs.get("abs-tol", 1e-12))

    def run(self) -> int:
        gold_data = self._read_csv(self._gold_path)
        test_data = self._read_csv(self._test_path)

        try:
            lines_to_check = self._resolve_lines(gold_data, test_data)
            cols_to_check = self._resolve_columns(gold_data, test_data)

            for row_idx in lines_to_check:
                for col in cols_to_check:
                    g_val = float(gold_data[row_idx][col])
                    t_val = float(test_data[row_idx][col])

                    rel = float(self._tolerances.get(col, {}).get("rel-tol", self._default_rel))
                    abs_ = float(self._tolerances.get(col, {}).get("abs-tol", self._default_abs))

                    if not math.isclose(g_val, t_val, rel_tol=rel, abs_tol=abs_):
                        self.output = (
                            f"Mismatch at row {row_idx}, column '{col}': "
                            f"gold={g_val}, test={t_val} "
                            f"(rel_tol={rel}, abs-tol={abs_})"
                        )
                        return -1

            self.output = "CSV files match within tolerance."
            return 0

        except Exception as ex:
            self.output = f"Comparison failed: {ex}"
            return -1

    def _read_csv(self, path):
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _resolve_lines(self, gold_data, test_data):
        max_len = min(len(gold_data), len(test_data))
        if self._lines == "all":
            return range(max_len)
        elif isinstance(self._lines, list):
            return [(i if i >= 0 else max_len + i) for i in self._lines]
        raise ValueError(f"Invalid lines selector: {self._lines}")

    def _resolve_columns(self, gold_data, test_data):
        all_cols = set(gold_data[0].keys()) & set(test_data[0].keys())
        if self._columns == "all":
            return all_cols
        elif isinstance(self._columns, list):
            return self._columns
        raise ValueError(f"Invalid columns selector: {self._columns}")
