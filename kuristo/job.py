import threading
import logging
import time
import os
from pathlib import Path
from kuristo.job_spec import JobSpec
from kuristo.action_factory import ActionFactory
from kuristo.context import Context
from kuristo.env import Env
from kuristo.utils import interpolate_str


class Job:
    """
    Job that is run by the scheduler
    """

    ID = 0

    # status
    WAITING = 0
    RUNNING = 1
    FINISHED = 2

    class TaggedFormatter(logging.Formatter):
        def format(self, record):
            if not hasattr(record, "tag"):
                record.tag = "INFO"  # fallback if not tagged
            return f"{self.formatTime(record)} - {record.tag:<12} - {record.getMessage()}"

    class Logger:
        """
        Simple encapsulation to simplify job logging into a file
        """

        def __init__(self, id, log_file):
            self._logger = logging.getLogger(f"JobLogger-{id}")
            self._logger.setLevel(logging.INFO)
            formatter = Job.TaggedFormatter()

            file_handler = logging.FileHandler(log_file, mode='w')
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

        def log(self, message, tag="INFO"):
            self._logger.info(message, extra={"tag": tag})

        def job_start(self, name):
            self.log(f"{name}", tag="JOB_START")

        def job_end(self):
            self.log("Done", tag="JOB_END")

        def task_start(self, name):
            self.log(f"* {name}", tag="TASK_START")

        def task_end(self, return_code):
            self.log(f"* Process completed with exit code {return_code}", tag="TASK_END")

        def script_line(self, cmd):
            self.log(f"> {cmd}", tag="SCRIPT")

        def output_line(self, line):
            self.log(line, tag="OUTPUT")

        def env(self, key, value):
            self.log(f"| {key}={value}")

        def dump(self, what):
            # dispatch types for dumping into a log file
            if isinstance(what, Env):
                self._dump_env(what)

        def _dump_env(self, env: Env):
            self.log("Environment variables:", tag="ENV")
            for key, value in env.items():
                self.env(key, value)

    def __init__(self, id, job_spec: JobSpec, log_dir: Path, matrix=None) -> None:
        """
        @param job_spec Job specification
        """
        Job.ID = Job.ID + 1
        self._num = Job.ID
        self._spec = job_spec
        self._env_file = log_dir / f"job-{self._num}.env"
        self._path_file = log_dir / f"job-{self._num}.path"
        self._thread = None
        self._process = None
        self._logger = self.Logger(
            self._num,
            log_dir / f'job-{self._num}.log'
        )
        self._return_code = None
        self._id = id
        self._name = self._create_job_name(job_spec, matrix)
        self._status = Job.WAITING
        self._skipped = False
        self._context = Context(
            base_env=self._get_base_env(),
            working_directory=job_spec.working_directory,
            defaults=job_spec.defaults,
            matrix=matrix
        )
        self._context.env.update((var, str(val)) for var, val in job_spec.env.items())
        self._steps = self._build_steps(job_spec)
        if job_spec.skip:
            self.skip(job_spec.skip_reason)
        self._step_task_ids = {}
        self._elapsed_time = 0.
        self._cancelled = threading.Event()
        self._timeout_timer = None
        self._step_lock = threading.Lock()
        self._active_step = None
        self._on_finish = self._noop
        self._on_step_start = self._noop
        self._on_step_finish = self._noop

    def start(self):
        """
        Run the job
        """
        self._status = Job.RUNNING
        self._thread = threading.Thread(target=self._target)
        self._thread.start()
        self._timeout_timer = threading.Timer(self.timeout_minutes * 60, self._on_timeout)
        self._timeout_timer.start()

    def wait(self):
        """
        Wait until the jobs is fnished
        """
        if self._thread is not None:
            self._thread.join()
            self._status = Job.FINISHED

    def skip(self, reason=None):
        """
        Mark this job as skipped
        """
        self._skipped = True
        if reason is None:
            self._skip_reason = "skipped"
        else:
            self._skip_reason = reason

    @property
    def spec(self):
        """
        Return job specification
        """
        return self._spec

    @property
    def name(self):
        """
        Return job name
        """
        return self._name

    @property
    def id(self):
        """
        Return job ID
        """
        return self._id

    @property
    def needs(self):
        """
        Return job IDs this job depends on
        """
        return self._spec.needs

    @property
    def timeout_minutes(self):
        """
        Return timeout in minutes
        """
        return self._spec.timeout_minutes

    @property
    def return_code(self):
        """
        Return code of the process
        """
        return self._return_code

    @property
    def num(self):
        """
        Return job number
        """
        return self._num

    @property
    def status(self):
        """
        Return job status
        """
        return self._status

    @property
    def is_skipped(self):
        """
        Return `True` if the job should be skipped
        """
        return self._skipped

    @property
    def skip_reason(self):
        """
        Return skip reason
        """
        return self._skip_reason

    @property
    def is_processed(self):
        """
        Check if the job is processed
        """
        return self._status == Job.FINISHED

    @property
    def required_cores(self):
        n_cores = 1
        for s in self._steps:
            n_cores = max(n_cores, s.num_cores)
        return n_cores

    @property
    def elapsed_time(self):
        """
        Return time it took to run this job
        """
        return self._elapsed_time

    @property
    def num_steps(self):
        return len(self._steps)

    @property
    def on_step_start(self):
        return self._on_step_start

    @on_step_start.setter
    def on_step_start(self, callback):
        self._on_step_start = callback

    @property
    def on_step_finish(self):
        return self._on_step_finish

    @on_step_finish.setter
    def on_step_finish(self, callback):
        self._on_step_finish = callback

    @property
    def on_finish(self):
        return self._on_finish

    @on_finish.setter
    def on_finish(self, callback):
        self._on_finish = callback

    def _target(self):
        start_time = time.perf_counter()
        self._return_code = 0
        self._run_process()
        end_time = time.perf_counter()
        self._elapsed_time = end_time - start_time
        self._finish_process()
        if self._timeout_timer is not None:
            self._timeout_timer.cancel()

    def _run_process(self):
        self._return_code = 0
        self._logger.job_start(self.name)
        for step in self._steps:
            with self._step_lock:
                self._active_step = step
            self._logger.task_start(step.name)
            self.on_step_start(self, step)
            try:
                if hasattr(step, 'command'):
                    for line in step.command.splitlines():
                        self._logger.script_line(line)
                exit_code = step.run()
            except Exception as e:
                self._logger.log(str(e))
                exit_code = -1
            self.on_step_finish(self, step)
            self._load_env()

            log_data = step.output
            for line in log_data.splitlines():
                self._logger.log(line)

            if self._cancelled.is_set():
                self._logger.log(f'* Job timed out after {self.timeout_minutes} minutes', tag="TASK_END")
                self._return_code = 124
                break
            elif exit_code == 124:
                self._logger.log(f'* Step timed out after {step.timeout_minutes} minutes', tag="TASK_END")
            else:
                self._logger.task_end(exit_code)

            if exit_code != 0 and not step.continue_on_error:
                self._return_code = exit_code
                break

        with self._step_lock:
            self._active_step = None
        if self._context:
            self._logger.dump(self._context.env)

    def skip_process(self):
        self._logger.job_start(self.name)
        self._logger.log(f'* Skipped: {self.skip_reason}', tag="TASK_END")
        self._logger.job_end()
        self._status = Job.FINISHED
        self._elapsed_time = 0.

    def _finish_process(self):
        self._status = Job.FINISHED
        self.on_finish(self)
        self._logger.job_end()

    def _on_timeout(self):
        """
        Called if the job runs longer than allowed.
        """
        with self._step_lock:
            if self._active_step is not None:
                self._cancelled.set()
                self._active_step.terminate()

    def _build_steps(self, spec):
        steps = []
        for step in spec.steps:
            action = ActionFactory.create(step, self._context)
            if action is not None:
                steps.append(action)
        return steps

    def _load_env(self):
        if self._env_file.exists():
            self._context.env.update_from_file(self._env_file)

        if self._path_file.exists():
            current_path = self._context.env.get("PATH", os.environ.get("PATH", ""))
            current = current_path.split(":")
            try:
                additional_paths = self._path_file.read_text().splitlines()
            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                self._logger.log(f"Error reading path file {self._path_file}: {e}", tag="ERROR")
                additional_paths = []
            for p in reversed(additional_paths):
                sanitized_path = p.strip()
                if os.path.isabs(sanitized_path) and os.path.exists(sanitized_path) and sanitized_path not in current:
                    current.insert(0, sanitized_path)
            self._context.env["PATH"] = ":".join(current)

    def _get_base_env(self):
        return {
            "KURISTO_ENV": self._env_file,
            "KURISTO_PATH": self._path_file,
            "KURISTO_JOB": self._name,
            "KURISTO_JOBID": self._num
        }

    def _noop(self, *args, **kwargs):
        pass

    def _create_job_name(self, job_spec, matrix):
        ipol_name = interpolate_str(job_spec.name, {"matrix" : matrix})
        if ipol_name == job_spec.name and matrix is not None:
            param_str = ",".join(f"{k}={v}" for k, v in matrix.items())
            return f"{job_spec.name}[{param_str}]"
        else:
            return ipol_name

    def create_step_tasks(self, progress):
        self._step_task_ids = {
            step.name: progress.add_task(
                f"  ↳ [magenta]{step.name}", total=None, visible=False
            )
            for step in self._steps
        }

    def step_task_id(self, step):
        return self._step_task_ids.get(step.name)


class JobJoiner:
    """
    Auxiliary class that is created in the background (i.e. not displayed to the user) and
    serves for defining dependencies between jobs that use `strategy.matrix`.
    There is no action that this class does. It really only serves for defining dependencies.

    For example:
    ```
    multiple-job:
      strategy:
        matrix:
          include:
            - animal: dog
              color: red
            - animal: cat
              color: black
    dep-job-a:
      needs: [multiple-job]
    ```
    The dependency graph then looks like this:
    ```
    multiple-job[red, dog]  ----+
                                +-->  multiple-job  -->  dep-job-a
    multiple-job[black, cat]  --+
    ```
    The `multiple-job` in the middle is represented by this class.
    """

    def __init__(self, id, spec: JobSpec, needs: list) -> None:
        """
        @param job_spec Job specification
        """
        Job.ID = Job.ID + 1
        self._num = Job.ID
        self._id = id
        self._name = id
        self._spec = spec
        self._status = Job.WAITING
        self._needs = needs

    @property
    def spec(self):
        """
        Return job specification
        """
        return self._spec

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
    def num(self):
        """
        Return job number
        """
        return self._num

    @property
    def is_skipped(self):
        """
        Return `True` if the job should be skipped
        """
        return False

    @property
    def is_processed(self):
        """
        Check if the job is processed
        """
        return self._status == Job.FINISHED

    @property
    def required_cores(self):
        return 0

    @property
    def num_steps(self):
        return 0

    @property
    def needs(self):
        """
        Return job IDs this job depends on
        """
        return self._needs

    @property
    def return_code(self):
        """
        Return code of the process
        """
        return 0

    @property
    def elapsed_time(self):
        """
        Return time it took to run this job
        """
        return 0

    @property
    def status(self):
        """
        Return job status
        """
        return self._status

    def create_step_tasks(self, progress):
        pass

    def start(self):
        self._status = Job.FINISHED
