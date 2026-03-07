import os
from pathlib import Path

import yaml

import kuristo.utils as utils


class Config:
    def __init__(self, no_ansi=True, path=None):
        self.no_ansi = no_ansi

        config_dir = utils.find_kuristo_root() or Path.cwd()
        if path:
            self.path = Path(path)
        else:
            self.path = Path(config_dir / "config.yaml")
        self._data = self._load()

        self.workflow_filename = self._get("base.workflow-filename", "kuristo.yaml")

        self.log_dir = (config_dir.parent / self._get("log.dir-name", ".kuristo-out")).resolve()
        self.log_history = self._get_int("log.history", 5)
        # Options: on_success, always, never
        self.log_cleanup = self._get("log.cleanup", "always")
        self.num_cores = self._resolve_cores()

        self.mpi_launcher = os.getenv(
            "KURISTO_MPI_LAUNCHER", self._get("runner.mpi-launcher", "mpirun")
        )

        self.batch_backend = self._get_str("batch.backend")
        self.batch_default_account = self._get_str("batch.default-account")
        self.batch_partition = self._get_str("batch.partition")

        self.console_width = self._get_int("base.console-width", 100)

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

    def _get_int(self, key: str, default: int) -> int:
        val = self._get(key, default)
        if not isinstance(val, int):
            raise TypeError(f"{key} must be an integer")
        return val

    def _get_str(self, key: str) -> str | None:
        val = self._get(key)
        if val is None:
            return None
        if not isinstance(val, str):
            raise TypeError(f"{key} must be a string")
        return val

    def _resolve_cores(self) -> int:
        system_default = utils.get_default_core_limit()
        value = self._get_int("resources.num-cores", system_default)

        try:
            value = int(value)
            if value <= 0 or value > os.cpu_count():
                raise ValueError
        except ValueError:
            print(
                f"Invalid 'resources.num-cores' value: {value}, falling back to system default ({system_default})"
            )
            return system_default

        return value


# Global config instance
_instance = Config()


def construct(args):
    """
    Construct config

    @param args Command line arguments
    """
    global _instance

    _instance = Config(no_ansi=args.no_ansi, path=args.config)


def get() -> Config:
    """
    Get configuration object

    @return Configuration object
    """
    return _instance
