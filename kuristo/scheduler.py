import logging
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

    def check(self):
        """
        Check that jobs can be run
        """
        self._check_for_cycles()
        self._check_oversized_jobs()
        self._skip_if_skipped_dependencies()

    def run_all_jobs(self):
        """
        Run all jobs in the queue
        """
        self._schedule_next_job()
        while any(not job.is_processed for job in self._graph.nodes):
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
        with self._lock:
            ready_jobs = self._get_ready_jobs()
            for job in ready_jobs:
                if len(self._active_jobs) < self._max_concurrent:
                    self._active_jobs.add(job)
                    logging.info(f"Starting job {job.id}...")
                    job.start()
                else:
                    break

    def _job_completed(self, job):
        with self._lock:
            logging.info(f'Job {job.id} finished with return code {job.return_code}')
            self._active_jobs.remove(job)
        self._schedule_next_job()

    def _check_for_cycles(self):
        """
        Check that jobs don't depend on each other
        """
        is_dag = netx.is_directed_acyclic_graph(self._graph)
        # TODO: improve this
        # - find what is depending on what and tell the user
        if not is_dag:
            logging.critical("Detected cyclic dependencies")
            raise SystemExit("Detected cyclic dependencies")

    def _check_oversized_jobs(self):
        """
        Mark jobs that are too big for the available resources as skipped
        """
        sources = [node for node in self._graph.nodes if self._graph.in_degree(node) == 0]
        for source in sources:
            for job in netx.dfs_tree(self._graph, source=source):
                if job.required_cores > self._resources.total_cores:
                    logging.info(f"Skipping job {job.id} (too big - requires {job.required_cores} cores)")
                    job.skip(f"Job too big (requires {job.required_cores} cores)")

    def _skip_if_skipped_dependencies(self):
        """
        If a job have skipped dependency, we would not be able to run it, so mark it as skipped as well
        """
        sources = [node for node in self._graph.nodes if self._graph.in_degree(node) == 0]
        for source in sources:
            for job in netx.dfs_tree(self._graph, source=source):
                predecessors = list(self._graph.predecessors(job))
                if any(dep.status == Job.SKIPPED for dep in predecessors):
                    logging.info(f"Skipping job {job.id} (skipped dependency)")
                    job.skip("Skipped dependency")
