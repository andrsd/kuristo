import threading
import logging
from .test_spec import TestSpec
from .action_factory import ActionFactory


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

    def __init__(self, test_spec: TestSpec) -> None:
        """
        @param test_spec Test specification
        """
        Job.ID = Job.ID + 1
        self._id = Job.ID
        self._on_finish_callback = None
        self._thread = None
        self._process = None
        self._stdout = None
        self._stderr = None
        self._logger = self.Logger(self._id, f'job-{self._id}.log')
        self._return_code = None
        if test_spec.name is None:
            self._name = "job" + str(self._id)
        else:
            self._name = test_spec.name
        self._status = Job.WAITING
        self._skipped = False
        self._steps = self._build_steps(test_spec)
        if test_spec.skip:
            self.skip(test_spec.skip_reason)

    def start(self):
        """
        Run the job
        """
        self._status = Job.RUNNING
        self._thread = threading.Thread(target=self._target)
        self._thread.start()

    def set_on_finish(self, callback):
        """
        Set the on_finish callback
        """
        self._on_finish_callback = callback

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

    def _target(self):
        self._return_code = 0
        if self._skipped:
            self._skip_process()
        else:
            self._run_process()
        self._finish_process();

    def _run_process(self):
        for step in self._steps:
            self._logger.log(f'* {step.name}...')
            step.run()

            log_data = step.stdout.decode()
            for line in log_data.splitlines():
                self._logger.log(line)

            self._logger.log(f'* Finished with return code {step.return_code}')
            self._return_code |= step.return_code

    def _skip_process(self):
        self._logger.log(f'* {self.name} was skipped: {self.skip_reason}')

    def _finish_process(self):
        self._status = Job.FINISHED
        if self._on_finish_callback is not None:
            self._on_finish_callback(self)

    def _build_steps(self, test_spec):
        steps = []
        for step in test_spec.steps:
            action = ActionFactory.create(step)
            if action is not None:
                steps.append(action)
        return steps

    @staticmethod
    def from_spec(ts):
        job = Job(ts)
        return job
