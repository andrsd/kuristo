from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScriptParameters:
    # Kuristo Run ID
    run_id: str
    # Job number we start numbering from
    first_job_num: int
    # Workflow file to execute
    workflow_file: Path
    # Job name
    name: str
    # Working directory
    work_dir: Path
    # Number of cores requested
    n_cores: int
    # Maximum time [mins]
    max_time: int
    # Partition name
    partition: Optional[str] = None


class BatchBackend(ABC):

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        """
        Return backend name
        """
        return self._name

    @abstractmethod
    def submit(self, params: ScriptParameters) -> str:
        """
        Submit a job script.

        @param params Script parameters
        @return Job ID from the queue
        """
        pass

    @abstractmethod
    def status(self, job_id: str) -> str:
        """
        Return job status.
        """
        pass
