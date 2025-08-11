import yaml
import os
from pathlib import Path
from kuristo.plugin_loader import find_kuristo_root
from kuristo.utils import get_default_core_limit


class Config:

    def __init__(self, path=None):
        base_dir = find_kuristo_root()
        self._config_dir = base_dir or Path.cwd()

        self.path = Path(path or self._config_dir / "config.yaml")
        self._data = self._load()

        self.workflow_filename = self._get("base.workflow-filename", "kuristo.yaml")

        self.log_dir = (self._config_dir.parent / self._get("log.dir_name", ".kuristo-out")).resolve()
        self.log_history = int(self._get("log.history", 5))
        # Options: on_success, always, never
        self.log_cleanup = self._get("log.cleanup", "always")
        self.num_cores = self._resolve_cores()

        self.mpi_launcher = os.getenv("KURISTO_MPI_LAUNCHER", self._get("runner.mpi_launcher", "mpirun"))

        self.batch_backend = self._get("batch.backend", None)
        self.batch_default_account = self._get("batch.default_account", None)
        self.batch_partition = self._get("batch.partition", None)

        self.console_width = self._get("base.console-width", 100)

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

    def _resolve_cores(self) -> int:
        system_default = get_default_core_limit()
        value = self._get("resources.num_cores", system_default)

        try:
            value = int(value)
            if value <= 0 or value > os.cpu_count():
                raise ValueError
        except ValueError:
            print(f"Invalid 'resources.num_cores' value: {value}, falling back to system default ({system_default})")
            return system_default

        return value

    def set_from_args(self, args):
        """
        Set configuration parameters from arguments passed via command line
        """
        self.no_ansi = args.no_ansi


# Global config instance
_instance = Config()


def get() -> Config:
    """
    Get configuration object

    @return Configuration object
    """
    return _instance
