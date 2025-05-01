import networkx as netx
import threading
from .job import Job


class Scheduler:
    """
    Job scheduler

    Jobs are added into a directed acyclic graph, so we can capture job dependencies.
    We start by running what ever jobs we can start. Every time job finishes, we schedule
    new one(s). We run until all jobs have FINISHED status.
    """

    def __init__(self, tests, rcs) -> None:
        """
        @param tests; [TestSpec] List of test speecifications
        @param rcs: Resources Resource to be scheduled
        """
        self._graph = netx.DiGraph()
        for ts in tests:
            self._add_job(ts)
        self._active_jobs = set()
        self._max_concurrent = 4
        self._lock = threading.Lock()
        self._resources = rcs

    def run_all_jobs(self):
        """
        Run all jobs in the queue
        """
        self._schedule_next_job()
        while any(job.status != Job.FINISHED for job in self._graph.nodes):
            threading.Event().wait(1)

    def _add_job(self, ts):
        """
        Add a job into the graph
        """
        job = Job.from_spec(ts)
        job.set_on_finish(self._job_completed)
        self._graph.add_node(job)
        # TODO: add job dependencies

    def _get_ready_jobs(self):
        """
        Find jobs whose dependencies are completed and are still waiting
        """
        ready_jobs = []
        for job in self._graph.nodes:
            if job.status == Job.WAITING:
                predecessors = list(self._graph.predecessors(job))
                if all(dep.status == Job.FINISHED for dep in predecessors):
                    ready_jobs.append(job)
        return ready_jobs

    def _schedule_next_job(self):
        ready_jobs = self._get_ready_jobs()
        for job in ready_jobs:
            if len(self._active_jobs) < self._max_concurrent:
                with self._lock:
                    self._active_jobs.add(job)
                    job.start()
            else:
                break

    def _job_completed(self, job):
        with self._lock:
            print(f"Job {job.id} finished with return code: {job.return_code}")
            self._active_jobs.remove(job)
        self._schedule_next_job()
