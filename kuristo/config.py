import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, PrivateAttr, ValidationError, field_validator

import kuristo.utils as utils
from kuristo.exceptions import UserException


class BaseConfigSection(BaseModel):
    workflow_filename: str = Field(alias="workflow-filename", default="kuristo.yaml")
    console_width: int = Field(alias="console-width", default=100)

    model_config = {"populate_by_name": True}


class LogConfigSection(BaseModel):
    dir_name: str = Field(alias="dir-name", default=".kuristo-out")
    history: int = 5
    cleanup: str = "always"

    model_config = {"populate_by_name": True}


class ResourcesConfigSection(BaseModel):
    num_cores: int = Field(alias="num-cores", default_factory=utils.get_default_core_limit)

    model_config = {"populate_by_name": True}

    @field_validator("num_cores", mode="before")
    @classmethod
    def validate_cores(cls, v):
        system_default = utils.get_default_core_limit()
        if v is None:
            return system_default
        try:
            val = int(v)
            if val <= 0 or (os.cpu_count() is not None and val > os.cpu_count()):
                print(
                    f"Invalid 'resources.num-cores' value: {val}, falling back to system default ({system_default})"
                )
                return system_default
            return val
        except (ValueError, TypeError):
            print(
                f"Invalid 'resources.num-cores' value: {v}, falling back to system default ({system_default})"
            )
            return system_default


class RunnerConfigSection(BaseModel):
    mpi_launcher: str = Field(alias="mpi-launcher", default="mpirun")

    model_config = {"populate_by_name": True}


class BatchConfigSection(BaseModel):
    backend: Optional[str] = None
    default_account: Optional[str] = Field(alias="default-account", default=None)
    partition: Optional[str] = None

    model_config = {"populate_by_name": True}


class Config(BaseModel):
    base: BaseConfigSection = Field(default_factory=BaseConfigSection)
    log: LogConfigSection = Field(default_factory=LogConfigSection)
    resources: ResourcesConfigSection = Field(default_factory=ResourcesConfigSection)
    runner: RunnerConfigSection = Field(default_factory=RunnerConfigSection)
    batch: BatchConfigSection = Field(default_factory=BatchConfigSection)

    no_ansi: bool = True
    path: Path = Path()

    _custom_path_provided: bool = PrivateAttr(default=False)

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

    def __init__(self, no_ansi=True, path=None, **kwargs):
        config_dir = utils.find_kuristo_root() or Path.cwd()
        custom_path_provided = False
        if path:
            path = Path(path)
            custom_path_provided = True
        else:
            path = Path(config_dir / "config.yaml")

        data = self._load_data(path, custom_path_provided)

        try:
            super().__init__(no_ansi=no_ansi, path=path, **data, **kwargs)
        except ValidationError as exp:
            msgs = []
            n = len(exp.errors())
            msgs.append(f"{n} validation error(s) found in configuration file {path}:")
            for error in exp.errors():
                loc_str = ".".join(str(p) for p in error["loc"])
                msgs.append(f"- {loc_str}: {error['msg']}")
            raise UserException("\n".join(msgs))

        self._custom_path_provided = custom_path_provided

    @staticmethod
    def _load_data(path: Path, custom_path_provided: bool) -> dict:
        try:
            with open(path, "r") as f:
                try:
                    data = yaml.safe_load(f) or {}
                    if not isinstance(data, dict):
                        raise UserException(
                            f"Configuration file {path} must contain a YAML dictionary"
                        )
                    return data
                except yaml.YAMLError as exp:
                    mark = getattr(exp, "problem_mark", None)
                    if mark:
                        line = mark.line + 1
                        column = mark.column + 1
                        err_msg = f"Configuration YAML syntax error in {path} at line {line}, column {column}:\n{exp}"
                    else:
                        err_msg = f"Configuration YAML parsing error in {path}:\n{exp}"
                    raise UserException(err_msg)
        except FileNotFoundError:
            if custom_path_provided:
                raise UserException(f"Configuration file not found: {path}")
            return {}
        except OSError as exp:
            raise UserException(f"Error reading configuration file {path}: {exp}")

    @property
    def workflow_filename(self) -> str:
        return self.base.workflow_filename

    @workflow_filename.setter
    def workflow_filename(self, value: str):
        self.base.workflow_filename = value

    @property
    def console_width(self) -> int:
        return self.base.console_width

    @console_width.setter
    def console_width(self, value: int):
        self.base.console_width = value

    @property
    def log_cleanup(self) -> str:
        return self.log.cleanup

    @property
    def log_history(self) -> int:
        return self.log.history

    @property
    def log_dir(self) -> Path:
        config_dir = utils.find_kuristo_root() or Path.cwd()
        return (config_dir.parent / self.log.dir_name).resolve()

    @property
    def mpi_launcher(self) -> str:
        return os.getenv("KURISTO_MPI_LAUNCHER", self.runner.mpi_launcher)

    @property
    def num_cores(self) -> int:
        return self.resources.num_cores

    @num_cores.setter
    def num_cores(self, value: int):
        self.resources.num_cores = value

    @property
    def batch_backend(self) -> Optional[str]:
        return self.batch.backend

    @batch_backend.setter
    def batch_backend(self, value: Optional[str]):
        self.batch.backend = value

    @property
    def batch_default_account(self) -> Optional[str]:
        return self.batch.default_account

    @batch_default_account.setter
    def batch_default_account(self, value: Optional[str]):
        self.batch.default_account = value

    @property
    def batch_partition(self) -> Optional[str]:
        return self.batch.partition

    @batch_partition.setter
    def batch_partition(self, value: Optional[str]):
        self.batch.partition = value


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
