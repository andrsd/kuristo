import queue
import threading
from .job import Job


class Scheduler:
    """
    Job scheduler
    """

    def __init__(self, tests, rcs) -> None:
        """
        @param tests; [TestSpec] List of test speecifications
        @param rcs: Resources Resource to be scheduled
        """
        self._job_queue = queue.Queue()
        for ts in tests:
            job = Job.from_spec(ts)
            job.set_on_finish(self._job_completed)
            self._job_queue.put(job)
        self._active_jobs = set()
        self._max_concurrent = 2
        self._lock = threading.Lock()
        self._resources = rcs

    def run_all_jobs(self):
        """
        Run all jobs in the queue
        """
        self._schedule_next_job()
        while self._active_jobs:
            threading.Event().wait(1)

    def _schedule_next_job(self):
        with self._lock:
            while not self._job_queue.empty() and len(self._active_jobs) < self._max_concurrent:
                job = self._job_queue.get()
                self._active_jobs.add(job)
                job.start()

    def _job_completed(self, job):
        with self._lock:
            print(f"Job {job.id} finished with return code: {job.return_code}")
            self._active_jobs.remove(job)
        self._schedule_next_job()
