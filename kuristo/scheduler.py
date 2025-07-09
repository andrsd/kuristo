import networkx as netx
import threading
import sys
import time
from pathlib import Path
from rich.progress import (Progress, SpinnerColumn, TextColumn, BarColumn, ProgressColumn, TimeElapsedColumn)
from rich.text import Text
from rich.console import Console
from rich.style import Style
from .job import Job
from itertools import product
from ._utils import rich_job_name, interpolate_str
from .config import Config
from .resources import Resources


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


class StepCountColumn(ProgressColumn):
    def render(self, task) -> Text:
        if task.total is not None:
            return Text(f"{int(task.completed)}/{int(task.total)}", style=Style(color="green"))
        else:
            return Text("")


class NullProgress:
    def __init__(self, no_ansi):
        self.console = Console(force_terminal=no_ansi, no_color=no_ansi, markup=no_ansi)

    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): pass
    def add_task(self, *args, **kwargs): pass
    def remove_task(self, *args, **kwargs): pass
    def update(self, *args, **kwargs): pass
    def advance(self, *args, **kwargs): pass
    def stop(self): pass


class Scheduler:
    """
    Job scheduler

    Jobs are added into a directed acyclic graph, so we can capture job dependencies.
    We start by running what ever jobs we can start. Every time job finishes, we schedule
    new one(s). We run until all jobs have FINISHED status.
    """

    def __init__(self, specs, rcs: Resources, log_dir, config: Config, no_ansi=False, report_path=None) -> None:
        """
        @param specs: [JobSpec] List of job specifications
        @param rcs: Resources Resource to be scheduled
        @param log_dir: Directory where we write logs
        @param config: Configuration
        @param job_times_path: File name to store timing report into
        """
        self._no_ansi = no_ansi
        self._log_dir = Path(log_dir)
        self._config = config
        self._create_graph(specs)
        self._active_jobs = set()
        self._lock = threading.Lock()
        self._resources = rcs
        if self._no_ansi:
            self._progress = NullProgress(no_ansi=no_ansi)
        else:
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(style=Style(color="grey23"), pulse_style=Style(color="grey46")),
                StepCountColumn(),
                TimeElapsedColumn(),
                transient=True
            )
        # tasks that are executed
        self._tasks = {}
        self._n_success = 0
        self._n_failed = 0
        self._n_skipped = 0
        #
        self._report_path = report_path

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
        self._print_time(end_time - start_time)
        self._write_report()

    def _create_graph(self, specs):
        self._graph = netx.DiGraph()
        job_map = {}
        for sp in specs:
            jobs = self._create_jobs(sp)
            for j in jobs:
                j.on_finish = self._job_completed
                j.on_step_start = self._on_step_start
                j.on_step_finish = self._on_step_finish
                self._graph.add_node(j)
                job_map[j.name] = j

        for sp in specs:
            for dep_name in sp.needs:
                if dep_name not in job_map:
                    # TODO: improve this error message (like tell the user which file this was found in)
                    raise ValueError(f"Job '{sp.name}' depends on unknown job '{dep_name}'")
                self._graph.add_edge(job_map[dep_name], job_map[sp.name])

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
                    job_id = self._padded_job_id(job)
                    job_name = rich_job_name(job.name)
                    self._progress.console.print(
                        Text.from_markup(f"[yellow]-[/] [{job_id}] [cyan not bold]{job_name}[/] was skipped: [cyan]{job.skip_reason}")
                    )
                    self._n_skipped = self._n_skipped + 1
                    continue

                required = job.required_cores
                if self._resources.available_cores >= required:
                    self._resources.allocate_cores(required)
                    self._active_jobs.add(job)
                    job_id = self._padded_job_id(job)
                    job_name = rich_job_name(job.name)
                    task_id = self._progress.add_task(
                        Text.from_markup(f"[cyan]{job_name}"),
                        total=job.num_steps
                    )
                    self._tasks[job.id] = task_id
                    job.create_step_tasks(self._progress)
                    job.start()
                    if self._no_ansi:
                        self._progress.console.print(
                            Text.from_markup(f"- [{job_id}] {job_name} started")
                        )

    def _job_completed(self, job):
        with self._lock:
            job_id = self._padded_job_id(job)
            job_name = rich_job_name(job.name)
            if job.return_code == 0:
                self._progress.console.print(
                    Text.from_markup(f"[green]✔[/] [{job_id}] [cyan not bold]{job_name}[/] finished with return code {job.return_code} [magenta not bold][{human_time2(job.elapsed_time)}][/]")
                )
                self._n_success = self._n_success + 1
            elif job.return_code == 124:
                self._progress.console.print(
                    Text.from_markup(f"[red]x[/] [{job_id}] [cyan not bold]{job_name}[/] timed out [magenta not bold][{human_time2(job.elapsed_time)}][/]")
                )
                self._n_failed = self._n_failed + 1
            else:
                self._progress.console.print(
                    Text.from_markup(f"[red]x[/] [{job_id}] [cyan not bold]{job_name}[/] finished with return code {job.return_code} [magenta not bold][{human_time2(job.elapsed_time)}][/]")
                )
                self._n_failed = self._n_failed + 1
            task_id = self._tasks[job.id]
            self._progress.remove_task(task_id)
            del self._tasks[job.id]
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

    def _print_stats(self):
        total = self._n_success + self._n_failed + self._n_skipped

        self._progress.console.print(
            Text.from_markup(
                f"[green]✔[/] Success: [green]{self._n_success:,}[/]    "
                f"[red]x[/] Failed: [red]{self._n_failed:,}[/]    "
                f"[yellow]-[/] Skipped: [yellow]{self._n_skipped:,}[/]    "
                f"Total: {total}"
            )
        )

    def _print_time(self, elapsed_time):
        self._progress.console.print(
            Text.from_markup(f"  Took: {human_time(elapsed_time)}")
        )

    def _create_log_dir(self):
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _padded_job_id(self, job):
        max_id_width = len(str(self._graph.number_of_nodes()))
        return f"{job.id:>{max_id_width}}"

    def _create_jobs(self, spec):
        """
        Create jobs

        @param spec Job specification
        @return List of `Job`s
        """
        if spec.strategy:
            matrix = spec.strategy.get("matrix", {})
            variants = self._expand_matrix_value(matrix)
            jobs = []
            for v in variants:
                name = self._build_matrix_job_name(spec.name, v)
                job = Job(name, spec, self._log_dir, self._config, matrix=v)
                jobs.append(job)
            return jobs
        else:
            job = Job(spec.name, spec, self._log_dir, self._config)
            return [job]

    def _build_matrix_job_name(self, base_name, combo):
        """
        Create job name for a job from a matrix

        @param base_name Base job name
        @param combo Combination of keys and values (k, v) with values form startegy.matrix
        @return Job name
        """
        ipol_name = interpolate_str(base_name, {"matrix" : combo})
        if ipol_name == base_name:
            param_str = ",".join(f"{k}={v}" for k, v in combo.items())
            return f"{base_name}[{param_str}]"
        else:
            return ipol_name

    def _expand_matrix_value(self, matrix):
        """
        Expand matrix specification into actual (key,value) pairs

        @param matrix specification
        @return List of combinations form the matrix
        """
        include = matrix.pop("include", [])
        # TODO: implement exclude
        keys = list(matrix.keys())
        values = list(matrix.values())

        variants = []
        seen = set()

        if keys and values:
            # build Cartesian product if we have keys and values
            for combo in product(*values):
                combo_dict = dict(zip(keys, combo))
                frozen = frozenset(combo_dict.items())
                if frozen not in seen:
                    variants.append(combo_dict)
                    seen.add(frozen)

        # Add explicit 'include' entries
        for extra in include:
            frozen = frozenset(extra.items())
            if frozen not in seen:
                variants.append(extra)

        return variants

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

        job_task_id = self._tasks[job.id]
        self._progress.update(job_task_id, advance=1)

    def _write_report(self):
        if self._report_path:
            self._write_report_csv(self._report_path)

    def _write_report_csv(self, csv_path: Path):
        import csv
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "job name", "status", "duration [s]", "return code"])
            for job in self._graph.nodes:
                duration = "" if job.is_skipped else round(job.elapsed_time, 3)
                if job.is_skipped:
                    status = "skipped"
                elif job.return_code == 0:
                    status = "success"
                else:
                    status = "failed"
                writer.writerow([job.id, job.name, status, duration, job.return_code])
