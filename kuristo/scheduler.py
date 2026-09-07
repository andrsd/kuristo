import asyncio
import time
from pathlib import Path

import networkx as netx
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.style import Style
from rich.text import Text

import kuristo.config as config
import kuristo.ui as ui
import kuristo.utils as utils
from kuristo.exceptions import UserException
from kuristo.job import Job, JobJoiner, create_job_graph
from kuristo.resources import Resources
from kuristo.workflow import Workflow


class StepCountColumn(ProgressColumn):
    def __init__(self, wd):
        super().__init__()
        self._width = wd

    def render(self, task) -> Text:
        if task.total is not None:
            completed = f"{int(task.completed):>{self._width}}"
            total = f"{int(task.total):>{self._width}}"
            return Text.from_markup(f"[ [green]{completed}/{total}[/] ] ")
        else:
            return Text("")


class NullProgress:
    def __init__(self):
        self.console = ui.console()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def add_task(self, *args, **kwargs):
        pass

    def remove_task(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def advance(self, *args, **kwargs):
        pass

    def stop(self):
        pass

    def refresh(self):
        pass


class AsyncResources:
    """
    An asynchronous resource manager wrapping Resources that supports non-blocking
    waits for core allocation.
    """

    def __init__(self, rcs: Resources) -> None:
        self._rcs = rcs
        self._condition = asyncio.Condition()
        self._waiting_priority = 0

    async def acquire(self, n: int, priority: bool = False):
        async with self._condition:
            if priority:
                self._waiting_priority += 1
            try:
                while self._rcs.available_cores < n or (
                    not priority and self._waiting_priority > 0
                ):
                    await self._condition.wait()
                self._rcs.allocate_cores(n)
            finally:
                if priority:
                    self._waiting_priority -= 1

    async def release(self, n: int):
        async with self._condition:
            self._rcs.free_cores(n)
            self._condition.notify_all()


class Scheduler:
    """
    Job scheduler

    Jobs are added into a directed acyclic graph, so we can capture job dependencies.
    We start by running what ever jobs we can start. Every time job finishes, we schedule
    new one(s). We run until all jobs have FINISHED status.
    """

    def __init__(
        self,
        workflows: list[Workflow],
        rcs: Resources,
        out_dir,
        labels: list[str] | None = None,
        job_nums: set[int] | None = None,
        priority_job_nums: set[int] | None = None,
    ) -> None:
        """
        @param workflows: [Workflows] List of workflows
        @param rcs: Resources Resource to be scheduled
        @param out_dir: Directory where we write logs
        @param labels: Optional list of labels to filter jobs
        @param job_nums: Optional set of job numbers to run (e.g., from --rerun-failed)
        @param priority_job_nums: Optional set of job numbers to run first (e.g., from --failed-first)
        @param config: Configuration
        @param job_times_path: File name to store timing report into
        """
        cfg = config.get()
        self._out_dir = Path(out_dir)
        self._priority_job_nums = priority_job_nums or set()
        self._graph = self._create_job_graph(workflows, labels, job_nums)
        self._max_label_len = cfg.console_width
        self._max_num_width = 1
        for job in self._graph.nodes:
            self._max_label_len = max(self._max_label_len, len(job.name) + 1)
            self._max_num_width = max(self._max_num_width, len(str(job.num)))

        self._resources = rcs
        if cfg.no_ansi:
            self._progress = NullProgress()
        else:
            self._progress = Progress(
                SpinnerColumn(),
                StepCountColumn(self._max_num_width),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(style=Style(color="grey23"), pulse_style=Style(color="grey46")),
                TextColumn(" "),
                TimeElapsedColumn(),
                transient=True,
                console=ui.console(),
            )
        # tasks that are executed
        self._tasks = {}
        self._n_success = 0
        self._n_failed = 0
        self._n_skipped = 0
        self._total_runtime = 0.0

    @property
    def total_runtime(self):
        return self._total_runtime

    @property
    def jobs(self):
        return self._graph.nodes

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
        self._create_out_dir()

        self._total_task_id = self._progress.add_task(
            "[bold]Total progress[/]",
            total=self._get_total_number_of_jobs(),
        )

        asyncio.run(self._run_all_jobs_async())

    async def _run_all_jobs_async(self):
        """
        Run jobs asynchronously
        """
        job_nodes = utils.topological_sort(self._graph)
        resources_async = AsyncResources(self._resources)
        start_time = time.perf_counter()
        tasks_dict = {}
        with self._progress:
            for job in job_nodes:
                tasks_dict[job] = asyncio.create_task(
                    self._run_job(job, tasks_dict, resources_async)
                )

            await asyncio.gather(*tasks_dict.values())
        end_time = time.perf_counter()
        self._total_runtime = end_time - start_time

    async def _run_job(self, job, tasks_dict, resources_async):
        # wait for all dependencies to complete
        predecessors = list(self._graph.predecessors(job))
        if predecessors:
            await asyncio.gather(*[tasks_dict[dep] for dep in predecessors])

        if job.is_skipped:
            job.skip_process()
            ui.status_line(job, "SKIP", self._max_num_width, self._max_label_len)
            self._n_skipped = self._n_skipped + 1
            return

        if isinstance(job, JobJoiner):
            job.start()
            return

        required = job.required_cores
        # wait for cores
        await resources_async.acquire(required)
        try:
            job_name = ui.job_name_markup(job.name)
            task_id = self._progress.add_task(
                f"[grey58]{ui.truncate_or_pad(job_name, self._max_label_len - 66)}[/]",
                total=job.num_steps,
            )
            self._tasks[job.num] = task_id

            ui.status_line(job, "STARTING", self._max_num_width, self._max_label_len)

            job.start()
            await asyncio.to_thread(job.wait)
        finally:
            await resources_async.release(required)

    def _create_job_graph(
        self,
        workflows: list[Workflow],
        labels: list[str] | None = None,
        job_nums: set[int] | None = None,
    ) -> netx.DiGraph:
        """
        Create directed graph of jobs that will be executed. Graph captures dependencies between jobs.
        """
        graph = create_job_graph(workflows, self._out_dir)
        if labels:
            graph = self._apply_label_filter(graph, labels)
        if job_nums:
            graph = self._apply_num_filter(graph, job_nums)
        for job in graph.nodes:
            job.on_finish = self._job_completed
            job.on_step_start = self._on_step_start
            job.on_step_finish = self._on_step_finish
        return graph

    def _apply_label_filter(self, graph: netx.DiGraph, labels: list[str]) -> netx.DiGraph:
        """
        Filter jobs based on labels, marking non-matching jobs as skipped.
        Includes all transitive dependencies of matching jobs.

        @param labels: List of labels to filter by (union - matches any label)
        """
        # Find all jobs with matching labels
        matching_jobs = set()
        for job in graph.nodes:
            if job.spec.labels:
                if any(label in job.spec.labels for label in labels):
                    matching_jobs.add(job)

        # Collect all transitive dependencies of matching jobs
        required_jobs = set(matching_jobs)
        to_visit = list(matching_jobs)
        visited = set()

        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for predecessor in graph.predecessors(current):
                if predecessor not in required_jobs:
                    required_jobs.add(predecessor)
                    to_visit.append(predecessor)

        # Skip all jobs not in required set
        nodes_to_remove = []
        for job in graph.nodes:
            if job not in required_jobs:
                nodes_to_remove.append(job)
        graph.remove_nodes_from(nodes_to_remove)
        return graph

    def _apply_num_filter(self, graph: netx.DiGraph, job_nums: set[int]) -> netx.DiGraph:
        """
        Filter jobs based on job numbers, including all transitive dependencies.
        Used for --rerun-failed to re-run failed jobs and their dependencies.

        @param job_nums: Set of job numbers to run (e.g., from previous run's report)
        """
        # Find all jobs whose number is in job_nums
        matching_jobs = {job for job in graph.nodes if job.num in job_nums}

        # Collect all transitive dependencies of matching jobs
        required_jobs = set(matching_jobs)
        to_visit = list(matching_jobs)
        visited = set()

        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for predecessor in graph.predecessors(current):
                if predecessor not in required_jobs:
                    required_jobs.add(predecessor)
                    to_visit.append(predecessor)

        # Remove all jobs not in required set
        nodes_to_remove = [job for job in graph.nodes if job not in required_jobs]
        graph.remove_nodes_from(nodes_to_remove)
        return graph

    def _job_completed(self, job):
        assert isinstance(job, Job)

        try:
            loop = asyncio.get_running_loop()
            loop.call_later(0.25, self._job_completed_sync, job)
        except RuntimeError:
            time.sleep(0.25)
            self._job_completed_sync(job)

    def _job_completed_sync(self, job):
        if job.return_code == 0:
            ui.status_line(job, "PASS", self._max_num_width, self._max_label_len)
            self._n_success = self._n_success + 1
        elif job.return_code == 124:
            ui.status_line(job, "TIMEOUT", self._max_num_width, self._max_label_len)
            self._n_failed = self._n_failed + 1
        else:
            ui.status_line(job, "FAIL", self._max_num_width, self._max_label_len)
            self._n_failed = self._n_failed + 1
        task_id = self._tasks[job.num]
        self._progress.remove_task(task_id)
        del self._tasks[job.num]
        self._progress.update(self._total_task_id, advance=1)

    def _check_for_cycles(self):
        """
        Check that jobs don't depend on each other
        """
        is_dag = netx.is_directed_acyclic_graph(self._graph)
        if not is_dag:
            try:
                cycle = netx.find_cycle(self._graph)
                readable = " → ".join(job.name for job, _ in cycle)
                raise UserException(f"Detected cyclic dependency: {readable}")
            except netx.exception.NetworkXNoCycle:
                raise UserException("Detected cyclic dependency")

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

    def _create_out_dir(self):
        self._out_dir.mkdir(parents=True, exist_ok=True)

    def exit_code(self, *, strict=False):
        """
        Return error code to report back into calling environment
        """
        if self._n_failed > 0:
            return 1
        if strict and self._n_skipped > 0:
            return 2
        return 0

    def _on_step_start(self, job, step):
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(self._progress.refresh)
        except RuntimeError:
            self._progress.refresh()

    def _on_step_finish(self, job, step):
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(self._on_step_finish_sync, job, step)
        except RuntimeError:
            self._on_step_finish_sync(job, step)

    def _on_step_finish_sync(self, job, step):
        assert isinstance(job, Job)

        job_task_num = self._tasks[job.num]
        self._progress.update(job_task_num, advance=1)
        self._progress.refresh()

    def _get_total_number_of_jobs(self):
        n_jobs = 0
        for job in self._graph.nodes:
            if isinstance(job, Job):
                n_jobs += 1
        return n_jobs

    def print_stats(self):
        """
        Print stats and total run time
        """
        ui.stats(
            ui.RunStats(
                n_success=self._n_success,
                n_failed=self._n_failed,
                n_skipped=self._n_skipped,
            )
        )
        ui.time(self._total_runtime)
