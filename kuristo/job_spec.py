import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field, PrivateAttr, ValidationError, model_validator
from typing import List, Optional, Union, Dict, Any
from itertools import product


class StrategyMatrix(BaseModel):
    include: Optional[List[dict]] = []
    raw_matrix: Optional[Dict[str, List[Any]]] = None

    @model_validator(mode="before")
    @classmethod
    def parse_matrix(cls, data):
        if "include" in data:
            return {"include": data["include"]}
        else:
            return {"raw_matrix": data}

    def combinations(self) -> List[Dict[str, Any]]:
        """
        Get combinations provided by the matrix
        """
        variants = []
        seen = set()

        if self.raw_matrix:
            keys = list(self.raw_matrix.keys())
            values = list(self.raw_matrix.values())

            # build Cartesian product if we have keys and values
            for combo in product(*values):
                combo_dict = dict(zip(keys, combo))
                frozen = frozenset(combo_dict.items())
                if frozen not in seen:
                    variants.append(combo_dict)
                    seen.add(frozen)

        # Add explicit 'include' entries
        if self.include:
            for extra in self.include:
                frozen = frozenset(extra.items())
                if frozen not in seen:
                    variants.append(extra)

        return variants


class Strategy(BaseModel):
    matrix: StrategyMatrix


class JobDefaultsRun(BaseModel):
    # Working directory
    working_directory: Optional[str] = Field(alias='working-directory', default=None)


class JobDefaults(BaseModel):
    run: JobDefaultsRun


class Step(BaseModel):
    """
    Data class with description of a job step
    """

    # Step description
    description: Optional[str] = ""
    # Step name
    name: Optional[str] = None
    # Action name to use
    uses: Optional[str] = None
    # Parameters used with action specified by 'uses'
    with_: Optional[dict] = Field(alias="with", default={})
    # Things to run (i.e. script)
    run: Optional[str] = None
    # Shell to use
    shell: Optional[str] = "sh"
    # Step ID
    id: Optional[str] = None
    # Working directory
    working_directory: Optional[str] = Field(alias='working-directory', default=None)
    # Timeout in minutes
    timeout_minutes: Optional[int] = Field(alias='timeout-minutes', default=60)
    # Continue on error
    continue_on_error: bool = Field(alias="continue-on-error", default=False)
    # Number of cores
    num_cores: int = Field(alias="num-cores", default=1)
    # Environment for this step
    env: Optional[dict] = Field(default={})

    model_config = {
        "populate_by_name": True
    }

    @property
    def params(self):
        """
        Return the step parameters
        """
        return self.with_

    @staticmethod
    def from_dict(**kwargs):
        step = Step(**kwargs)
        return step


class JobSpec(BaseModel):
    """
    Data class with a job specification
    """

    # Job description
    description: str = ""
    # Job steps
    steps: List[Step]
    # Should the job be skipped?
    skip_: Optional[str] = Field(alias='skip', default=None)
    # Timeout in minutes
    timeout_minutes: int = Field(alias='timeout-minutes', default=60)
    # Strategy
    strategy: Optional[Strategy] = None
    #
    needs_: Optional[Union[str, List[str]]] = Field(alias='needs', default=None)
    # Job ID
    _id: str = PrivateAttr()
    # Job name
    _name: str = PrivateAttr()
    # File name where the job specification was defined
    _file_name: str = PrivateAttr()
    # Environment for this job
    env: Optional[dict] = Field(default={})
    # Defaults
    defaults: Optional[JobDefaults] = None

    @property
    def id(self):
        """
        Return job ID
        """
        return self._id

    @property
    def name(self):
        """
        Return job name
        """
        return self._name

    @property
    def needs(self) -> List[str]:
        if self.needs_ is None:
            return []
        elif isinstance(self.needs_, str):
            return [self.needs_]
        else:
            return self.needs_

    @property
    def skip(self):
        """
        Should the job be skipped?
        """
        return self.skip_ is not None

    @property
    def skip_reason(self):
        """
        Return the reason why job is marked as skipped
        """
        return self.skip_

    @property
    def file_name(self):
        """
        Return file name where this job specification was
        """
        return self._file_name

    @property
    def working_directory(self):
        """
        Return file name where this job specification was
        """
        return self._work_dir

    def set_id(self, id):
        self._id = id

    def set_name(self, name: str):
        self._name = name

    def set_file_name(self, file_name):
        self._file_name = file_name

    def set_working_directory(self, work_dir: str):
        self._work_dir = work_dir

    def build_matrix_values(self):
        """
        Build matrix values

        @return list[tuple[str, dict | None]] first entry is the job name, second is the variant that has keys and values
        """
        variants = self._expand_matrix_value()
        jobs = []
        for v in variants:
            id = self._build_matrix_job_id(v)
            job = (id, v)
            jobs.append(job)
        return jobs

    def _expand_matrix_value(self):
        """
        Expand matrix specification into actual (key,value) pairs

        @return List of combinations from the matrix
        """
        if self.strategy:
            return self.strategy.matrix.combinations()
        else:
            return []

    def _build_matrix_job_id(self, variant):
        """
        Create job name for a job from a matrix

        @param variant Combination of keys and values (k, v) with values form startegy.matrix
        @return Job name
        """
        param_str = ",".join(f"{k}={v}" for k, v in variant.items())
        return f"{self.id}[{param_str}]"

    @staticmethod
    def from_dict(file_name, id, data):
        if isinstance(data, dict):
            ts = JobSpec(**data)
            ts.set_file_name(file_name)
            ts.set_working_directory(os.path.dirname(os.path.abspath(file_name)))
            ts.set_id(id)
            ts.set_name(data.get("name", id))
            return ts
        else:
            raise RuntimeError("Expected dict as 'data'")


def parse_workflow_files(workflow_files: list[Path]) -> list[JobSpec]:
    """
    Parse workflow files (kuristo.yaml)
    """
    specs = []
    for file in workflow_files:
        specs.extend(specs_from_file(file))
    return specs


def specs_from_file(file_path) -> list[JobSpec]:
    location = os.path.dirname(file_path)
    specs = []
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
        if data is not None:
            jobs = data.get('jobs', {})
            for id, params in jobs.items():
                try:
                    jspec = JobSpec.from_dict(file_path, id, params)
                    specs.append(jspec)
                except ValidationError as exp:
                    msgs = []
                    n = len(exp.errors())
                    msgs.append(f"{n} syntax error found in {location}:")
                    for error in exp.errors():
                        loc_str = ".".join(str(p) for p in error['loc'])
                        msgs.append(f"- {loc_str}: {error['msg']}")
                    raise RuntimeError("\n".join(msgs))
    return specs
