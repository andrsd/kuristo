import networkx as netx
import threading
import sys
import time
from pathlib import Path
from kuristo.job_spec import JobSpec
from rich.progress import (Progress, SpinnerColumn, TextColumn, BarColumn, ProgressColumn, TimeElapsedColumn)
from rich.text import Text
from rich.style import Style
import kuristo.ui as ui
import kuristo.config as config
from kuristo.job import Job, JobJoiner
from kuristo.resources import Resources


class StepCountColumn(ProgressColumn):
    def render(self, task) -> Text:
        if task.total is not None:
            return Text(f"{int(task.completed)}/{int(task.total)}", style=Style(color="green"))
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


class Scheduler:
    """
    Job scheduler

    Jobs are added into a directed acyclic graph, so we can capture job dependencies.
    We start by running what ever jobs we can start. Every time job finishes, we schedule
    new one(s). We run until all jobs have FINISHED status.
    """

    def __init__(self, specs, rcs: Resources, out_dir) -> None:
        """
        @param specs: [JobSpec] List of job specifications
        @param rcs: Resources Resource to be scheduled
        @param out_dir: Directory where we write logs
        @param config: Configuration
        @param job_times_path: File name to store timing report into
        """
        cfg = config.get()
        self._max_label_len = cfg.console_width
        self._max_id_width = 1
        self._out_dir = Path(out_dir)
        self._create_graph(specs)
        self._active_jobs = set()
        self._lock = threading.Lock()
        self._resources = rcs
        if cfg.no_ansi:
            self._progress = NullProgress()
        else:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(style=Style(color="grey23"), pulse_style=Style(color="grey46")),
                StepCountColumn(),
                TimeElapsedColumn(),
                transient=True
            )
            ui.set_console(self._progress.console)
        # tasks that are executed
        self._tasks = {}
        self._n_success = 0
        self._n_failed = 0
        self._n_skipped = 0
        self._total_runtime = 0.

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
        cfg = config.get()

        self._create_out_dir()
        start_time = time.perf_counter()
        with self._progress:
            while any(not job.is_processed for job in self._graph.nodes):
                self._schedule_next_job()
                threading.Event().wait(0.5)
        end_time = time.perf_counter()
        self._total_runtime = end_time - start_time
        if cfg.no_ansi:
            self._progress.console.print("")

        ui.line(cfg.console_width)
        ui.stats(ui.RunStats(
            n_success=self._n_success,
            n_failed=self._n_failed,
            n_skipped=self._n_skipped
        ))
        ui.time(self._total_runtime)

    def _create_graph(self, specs):
        self._graph = netx.DiGraph()
        job_map = {}
        for sp in specs:
            spec_jobs = create_jobs(sp, self._out_dir)
            for job in spec_jobs:
                job.on_finish = self._job_completed
                job.on_step_start = self._on_step_start
                job.on_step_finish = self._on_step_finish
                self._graph.add_node(job)
                job_map[job.id] = job
                self._max_label_len = max(self._max_label_len, len(job.name) + 1)
        self._max_id_width = len(str(self._graph.number_of_nodes()))

        for job in self._graph.nodes:
            for dep_name in job.needs:
                if dep_name not in job_map:
                    raise ValueError(f"{job.spec.file_name}: Job '{job.spec.id}' depends on unknown job '{dep_name}'")
                self._graph.add_edge(job_map[dep_name], job_map[job.id])

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
                if job.is_skipped:
                    job.skip_process()
                    ui.status_line(job, "SKIP", self._max_id_width, self._max_label_len)
                    self._n_skipped = self._n_skipped + 1
                    continue

                if isinstance(job, JobJoiner):
                    job.start()
                else:
                    required = job.required_cores
                    if self._resources.available_cores >= required:
                        self._resources.allocate_cores(required)
                        self._active_jobs.add(job)
                        job_name = ui.job_name_markup(job.name)
                        task_id = self._progress.add_task(
                            Text.from_markup(f"[cyan]{job_name}[/]"),
                            total=job.num_steps
                        )
                        self._tasks[job.num] = task_id
                        job.create_step_tasks(self._progress)
                        job.start()
                        ui.status_line(job, "STARTING", self._max_id_width, self._max_label_len)

    def _job_completed(self, job):
        with self._lock:
            if job.return_code == 0:
                ui.status_line(job, "PASS", self._max_id_width, self._max_label_len)
                self._n_success = self._n_success + 1
            elif job.return_code == 124:
                ui.status_line(job, "TIMEOUT", self._max_id_width, self._max_label_len)
                self._n_failed = self._n_failed + 1
            else:
                ui.status_line(job, "FAIL", self._max_id_width, self._max_label_len)
                self._n_failed = self._n_failed + 1
            task_id = self._tasks[job.num]
            self._progress.remove_task(task_id)
            del self._tasks[job.num]
            self._active_jobs.remove(job)
            self._resources.free_cores(job.required_cores)
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

    def _create_out_dir(self):
        self._out_dir.mkdir(parents=True, exist_ok=True)

    def exit_code(self, *, strict=False):
        if self._n_failed > 0:
            return 1
        if strict and self._n_skipped > 0:
            return 2
        return 0

    def _on_step_start(self, job, step):
        step_task_id = job.step_task_id(step)
        self._progress.update(step_task_id, visible=True)

    def _on_step_finish(self, job, step):
        step_task_id = job.step_task_id(step)
        self._progress.remove_task(step_task_id)

        job_task_num = self._tasks[job.num]
        self._progress.update(job_task_num, advance=1)


def create_jobs(spec: JobSpec, out_dir: Path):
    """
    Create jobs

    @param spec Job specification
    @return List of `Job`s
    """
    jobs = []
    if spec.strategy:
        needs = []
        for id, variant in spec.build_matrix_values():
            j = Job(id, spec, out_dir, matrix=variant)
            jobs.append(j)
            needs.append(id)
        jobs.append(JobJoiner(spec.id, spec, needs))
    else:
        jobs.append(Job(spec.id, spec, out_dir))
    return jobs
