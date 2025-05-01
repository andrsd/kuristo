import subprocess
import threading
from .runner import Runner


class Job:
    """
    Job that is run by the scheduler
    """

    ID = 0

    # status
    WAITING = 0
    RUNNING = 1
    FINISHED = 2

    def __init__(self, runner) -> None:
        """
        @param runner Runner that will execute the job
        """
        self._on_finish_callback = None
        self._runner = runner
        self._thread = None
        self._process = None
        self._stdout = None
        self._stderr = None
        self._return_code = None
        Job.ID = Job.ID + 1
        self._id = Job.ID
        self._name = "job" + str(self._id)
        self._status = Job.WAITING

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

    def _target(self):
        print(f"Job {self.id} started")
        self._run_process()
        self._run_checks()
        self._status = Job.FINISHED
        if self._on_finish_callback is not None:
            self._on_finish_callback(self)

    def _run_process(self):
        self._process = subprocess.Popen(self._runner.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._stdout, self._stderr = self._process.communicate()
        self._return_code = self._process.returncode

    def _run_checks(self):
        pass

    @staticmethod
    def from_spec(ts):
        runner = Runner()
        return Job(runner)
