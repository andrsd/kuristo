import os
from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, PrivateAttr, ValidationError

from kuristo.job_spec import JobSpec


class Workflow(BaseModel):
    # Workflow name
    name: Optional[str] = None
    # Workflow description
    description: str = ""
    # Job steps
    jobs: Dict[str, JobSpec]

    _file_name: str = PrivateAttr()

    model_config = {"populate_by_name": True}

    @property
    def file_name(self):
        """
        Return file name where this job specification was
        """
        return self._file_name

    def set_file_name(self, file_name):
        self._file_name = file_name

    @staticmethod
    def from_dict(file_name, data):
        if isinstance(data, dict):
            wf = Workflow(**data)
            wf.set_file_name(file_name)
            for name, job in wf.jobs.items():
                job.set_id(name)
                job.set_working_directory(os.path.dirname(os.path.abspath(file_name)))
            return wf
        else:
            raise RuntimeError("Expected dict as 'data'")


def parse_workflow_files(workflow_files: list[Path]) -> list[Workflow]:
    """
    Parse workflow files
    """
    workflows = []
    for file in workflow_files:
        wf = workflow_from_file(file)
        if wf is not None:
            workflows.append(wf)
    return workflows


def workflow_from_file(file_path: Path) -> Workflow | None:
    location = os.path.dirname(file_path)
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
        if data is not None:
            try:
                workflow = Workflow.from_dict(file_path, data)
                return workflow
            except ValidationError as exp:
                msgs = []
                n = len(exp.errors())
                msgs.append(f"{n} syntax error found in {location}:")
                for error in exp.errors():
                    loc_str = ".".join(str(p) for p in error["loc"])
                    msgs.append(f"- {loc_str}: {error['msg']}")
                raise RuntimeError("\n".join(msgs))
        else:
            return None
