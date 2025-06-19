import networkx as netx
import threading
import sys
import time
from pathlib import Path
from rich.progress import (Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn)
from rich.console import Console
from rich.table import Table
from rich.style import Style
from rich.panel import Panel
from .job import Job


def human_time(elapsed_time: float) -> str:
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if hours:
        parts.append(f"{int(hours)}h")
    if minutes:
        parts.append(f"{int(minutes)}m")
    parts.append(f"{seconds:.2f}s")

    return " ".join(parts)


def human_time2(elapsed_time: float) -> str:
    return f"{elapsed_time:.2f}s"


class Scheduler:
    """
    Job scheduler

    Jobs are added into a directed acyclic graph, so we can capture job dependencies.
    We start by running what ever jobs we can start. Every time job finishes, we schedule
    new one(s). We run until all jobs have FINISHED status.
    """

    def __init__(self, tests, rcs, log_dir) -> None:
        """
        @param tests; [TestSpec] List of test speecifications
        @param rcs: Resources Resource to be scheduled
        """
        self._log_dir = Path(log_dir)
        self._create_graph(tests)
        self._active_jobs = set()
        self._max_concurrent = 4
        self._lock = threading.Lock()
        self._resources = rcs
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(style=Style(color="grey23"), pulse_style=Style(color="grey46")),
            TimeElapsedColumn(),
            transient=True
        )
        self._tasks = {}
        self._n_success = 0
        self._n_failed = 0
        self._n_skipped = 0

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
        self._create_log_dir()
        start_time = time.perf_counter()
        with self._progress:
            self._schedule_next_job()
            while any(not job.is_processed for job in self._graph.nodes):
                threading.Event().wait(0.5)
        end_time = time.perf_counter()
        self._print_stats()
        print()
        self._print_time(end_time - start_time)

    def _create_graph(self, tests):
        self._graph = netx.DiGraph()
        job_map = {}
        for ts in tests:
            job = Job.from_spec(ts, self._log_dir)
            job.set_on_finish(self._job_completed)
            self._graph.add_node(job)
            job_map[job.name] = job

        for ts in tests:
            for dep_name in ts.needs:
                if dep_name not in job_map:
                    # TODO: improve this error message (like tell the user which file this was found in)
                    raise ValueError(f"Job '{ts.name}' depends on unknown job '{dep_name}'")
                self._graph.add_edge(job_map[dep_name], job_map[ts.name])

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
                    task_id = self._progress.add_task(f"[cyan]{job.name}", total=None)
                    self._tasks[job.id] = task_id
                    job.start()
                else:
                    break

    def _job_completed(self, job):
        with self._lock:
            if job.is_skipped:
                self._progress.console.print(f"[yellow]-[/] [{job.id}] [cyan not bold]{job.name}[/] was skipped: [cyan]{job.skip_reason}")
                self._n_skipped = self._n_skipped + 1
            elif job.return_code == 0:
                self._progress.console.print(f"[green]✔[/] [{job.id}] [cyan not bold]{job.name}[/] finished with return code {job.return_code} [magenta not bold][{human_time2(job.elapsed_time)}][/]")
                self._n_success = self._n_success + 1
            else:
                self._progress.console.print(f"[red]x[/] [{job.id}] [cyan not bold]{job.name}[/] finished with return code {job.return_code} [magenta not bold][{human_time2(job.elapsed_time)}][/]")
                self._n_failed = self._n_failed + 1
            task_id = self._tasks[job.id]
            self._progress.remove_task(task_id)
            del self._tasks[job.id]
            self._active_jobs.remove(job)
        self._schedule_next_job()

    def _check_for_cycles(self):
        """
        Check that jobs don't depend on each other
        """
        is_dag = netx.is_directed_acyclic_graph(self._graph)
        if not is_dag:
            try:
                cycle = netx.find_cycle(self._graph)
                readable = " → ".join(job.name for job, _ in cycle)
                sys.exit(f"Detected cyclic dependency: {readable}")
            except netx.exception.NetworkXNoCycle:
                sys.exit("Detected cyclic dependency")

    def _check_oversized_jobs(self):
        """
        Mark jobs that are too big for the available resources as skipped
        """
        sources = [node for node in self._graph.nodes if self._graph.in_degree(node) == 0]
        for source in sources:
            for job in netx.dfs_tree(self._graph, source=source):
                if job.required_cores > self._resources.total_cores:
                    job.skip(f"Job too big (requires {job.required_cores} cores)")

    def _skip_if_skipped_dependencies(self):
        """
        If a job have skipped dependency, we would not be able to run it, so mark it as skipped as well
        """
        sources = [node for node in self._graph.nodes if self._graph.in_degree(node) == 0]
        for source in sources:
            for job in netx.dfs_tree(self._graph, source=source):
                predecessors = list(self._graph.predecessors(job))
                if any(dep.is_skipped for dep in predecessors):
                    job.skip("Skipped dependency")

    def _print_stats(self):
        total = self._n_success + self._n_failed + self._n_skipped

        console = Console()
        console.print(
            f"[green]✔[/] Success: [green]{self._n_success:,}[/]    "
            f"[red]x[/] Failed: [red]{self._n_failed:,}[/]    "
            f"[yellow]-[/] Skipped: [yellow]{self._n_skipped:,}[/]    "
            f"Total: {total}"
        )

    def _print_time(self, elapsed_time):
        print(f"  Took: {human_time(elapsed_time)}")

    def _create_log_dir(self):
        self._log_dir.mkdir(parents=True, exist_ok=True)
