

class Env:
    """
    Environment
    """

    def __init__(self, base=None):
        self._vars = {}
        if isinstance(base, dict):
            for k, v in base.items():
                self[k] = v

    def get(self, key: str, default=None):
        return self._vars.get(key, default)

    def set(self, key: str, value: str):
        self._vars[key] = str(value)

    def update_from_file(self, path):
        if not path.exists():
            return
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                self.set(k.strip(), v.strip())

    def update(self, vals: dict):
        self._vars.update(vals)

    def as_dict(self):
        return dict(self._vars)

    def __getitem__(self, key) -> str:
        return self._vars[key]

    def __setitem__(self, key, value):
        self._vars[key] = str(value)

    def __contains__(self, key):
        return key in self._vars

    def __delitem__(self, key):
        del self._vars[key]

    def keys(self):
        return self._vars.keys()

    def items(self):
        return self._vars.items()

    def values(self):
        return self._vars.values()

    def __repr__(self):
        return f"Env({self._vars})"
