import threading
import logging
import time
from pathlib import Path
from .job_spec import JobSpec
from .action_factory import ActionFactory
from .context import Context
from .env import Env
from .config import Config


class Job:
    """
    Job that is run by the scheduler
    """

    ID = 0

    # status
    WAITING = 0
    RUNNING = 1
    FINISHED = 2

    class Logger:
        """
        Simple encapsulation to simplify job logging into a file
        """

        def __init__(self, id, log_file):
            self._logger = logging.getLogger(f"JobLogger-{id}")
            self._logger.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

            file_handler = logging.FileHandler(log_file, mode='w')
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

        def log(self, message):
            self._logger.info(message)

        def dump(self, what):
            # dispatch types for dumping into a log file
            if isinstance(what, Env):
                self._dump_env(what)

        def _dump_env(self, env: Env):
            self._logger.info("Environment variables:")
            for key, value in env.items():
                self._logger.info(f"| {key}={value}")

    def __init__(self, name, job_spec: JobSpec, log_dir: Path, config: Config, matrix=None) -> None:
        """
        @param job_spec Job specification
        """
        Job.ID = Job.ID + 1
        self._id = Job.ID
        self._env_file = log_dir / f"job-{self._id}.env"
        self._thread = None
        self._process = None
        self._stdout = None
        self._stderr = None
        self._logger = self.Logger(
            self._id,
            log_dir / f'job-{self._id}.log'
        )
        self._return_code = None
        if name is None:
            self._name = "job" + str(self._id)
        else:
            self._name = name
        self._status = Job.WAITING
        self._skipped = False
        self._context = Context(
            config=config,
            base_env=self._get_base_env(),
            matrix=matrix
        )
        self._steps = self._build_steps(job_spec)
        if job_spec.skip:
            self.skip(job_spec.skip_reason)
        self._step_task_ids = {}
        self._elapsed_time = 0.
        self._cancelled = threading.Event()
        self._timeout_timer = None
        self._timeout_minutes = job_spec.timeout_minutes
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
        self._timeout_timer = threading.Timer(self._timeout_minutes * 60, self._on_timeout)
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
    def name(self):
        """
        Return job name
        """
        return self._name

    @property
    def return_code(self):
        """
        Return code of the process
        """
        return self._return_code

    @property
    def id(self):
        """
        Return job ID
        """
        return self._id

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
        for step in self._steps:
            with self._step_lock:
                self._active_step = step
            self._logger.log(f'* {step.name}...')
            if hasattr(step, 'command'):
                for line in step.command.splitlines():
                    self._logger.log(f'> {line}')
            self.on_step_start(self, step)
            step.run(context=self._context)
            self.on_step_finish(self, step)
            self._load_env()

            log_data = step.output.decode()
            for line in log_data.splitlines():
                self._logger.log(line)

            if self._cancelled.is_set():
                self._logger.log(f'* Job timed out after {self._timeout_minutes} minutes')
                self._return_code = 124
            elif step.return_code == 124:
                self._logger.log(f'* Step timed out after {step.timeout_minutes} minutes')
            else:
                self._logger.log(f'* Finished with return code {step.return_code}')
                self._return_code |= step.return_code

        with self._step_lock:
            self._active_step = None
        if self._context:
            self._logger.dump(self._context.env)

    def skip_process(self):
        self._logger.log(f'* {self.name} was skipped: {self.skip_reason}')
        self._status = Job.FINISHED
        self._elapsed_time = 0.

    def _finish_process(self):
        self._status = Job.FINISHED
        self.on_finish(self)

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

    def _get_base_env(self):
        return {
            "KURISTO_ENV": self._env_file,
            "KURISTO_JOB": self._name,
            "KURISTO_JOBID": self._id
        }

    def _noop(self, *args, **kwargs):
        pass

    def create_step_tasks(self, progress):
        self._step_task_ids = {
            step.name: progress.add_task(
                f"  ↳ [magenta]{step.name}", total=None, visible=False
            )
            for step in self._steps
        }

    def step_task_id(self, step):
        return self._step_task_ids.get(step.name)
