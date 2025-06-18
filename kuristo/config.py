import yaml
from pathlib import Path
from ._plugin_loader import find_kuristo_root


class Config:
    def __init__(self, path=None):
        self._base_dir = find_kuristo_root()
        self._config_dir = self._base_dir or Path.cwd()

        self.path = Path(path or self._config_dir / "config.yaml")
        self._data = self._load()

        self.log_dir = (self._config_dir.parent / self._get("log.dir_name", ".kuristo-out")).resolve()
        self.log_history = int(self._get("log.history", 5))
        # Options: on_success, always, never
        self.log_cleanup = self._get("log.cleanup", "always")

    def _load(self):
        try:
            with open(self.path, "r") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def _get(self, key, default=None):
        parts = key.split(".")
        val = self._data
        for part in parts:
            if not isinstance(val, dict):
                return default
            val = val.get(part, default)
        return val
