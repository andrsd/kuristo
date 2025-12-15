from dataclasses import dataclass
from rich.console import Console
from rich.text import Text
import kuristo.config as config
from kuristo.job import Job, JobJoiner
from kuristo.utils import human_time


_console_instance = None


def console() -> Console:
    global _console_instance
    if _console_instance is None:
        cfg = config.get()
        _console_instance = Console(
            force_terminal=not cfg.no_ansi,
            no_color=cfg.no_ansi,
            markup=not cfg.no_ansi,
        )
    return _console_instance


def set_console(console: Console):
    global _console_instance
    _console_instance = console


@dataclass
class RunStats:
    # Number of successful
    n_success: int
    # NUmber of failed
    n_failed: int
    # Number of skipped
    n_skipped: int


def _padded_job_id(job_id, max_width):
    return f"{job_id:>{max_width}}"


def job_name_markup(job_name):
    return job_name.replace("[", "\\[")


def status_line(job, state, max_id_width, max_label_len):
    cfg = config.get()
    consol = console()
    if isinstance(job, Job):
        job_id = _padded_job_id(job.num, max_id_width)
        job_name_len = len(job.name)
        job_name = job_name_markup(job.name)
        if job.is_skipped:
            skip_reason = job.skip_reason
        else:
            skip_reason = ""
        elapsed_time = job.elapsed_time
    elif isinstance(job, dict):
        job_id = _padded_job_id(job["id"], max_id_width)
        job_name_len = len(job["job-name"])
        job_name = job_name_markup(job["job-name"])
        if job['status'] == 'skipped':
            skip_reason = job["reason"]
        else:
            skip_reason = ""
        elapsed_time = job.get("duration", 0.0)
    elif isinstance(job, JobJoiner):
        return
    else:
        raise ValueError("job parameter must be a dict of Job")
    time_str = human_time(elapsed_time)
    width = max_label_len - 15 - job_name_len - len(time_str)
    dots = "." * width

    if state == "STARTING":
        if cfg.no_ansi:
            markup = f"         #{job_id} {job_name} "
            consol.print(Text.from_markup(markup))
    else:
        markup = ""
        if state == "SKIP":
            markup += "\\[ [yellow]SKIP[/] ]"
        elif state == "PASS":
            markup += "\\[ [green]PASS[/] ]"
        elif state == "FAIL" or state == "TIMEOUT":
            markup += "\\[ [red]FAIL[/] ]"

        markup += f" [grey46]#{job_id}[/]"
        markup += f" [cyan bold]{job_name}[/]"
        if state == "SKIP":
            markup += f": [cyan]{skip_reason}"
        elif state == "TIMEOUT":
            markup += f" [grey23]{dots}[/]"
            markup += " timeout"
        else:
            markup += f" [grey23]{dots}[/]"
            markup += f" {time_str}"
        consol.print(Text.from_markup(markup))


def line(width: int):
    consol = console()

    line = "-" * width
    consol.print(
        Text.from_markup(f"[grey23]{line}[/]")
    )


def stats(stats: RunStats):
    consol = console()

    total = stats.n_success + stats.n_failed + stats.n_skipped

    consol.print(
        Text.from_markup(
            f"[grey46]Success:[/] [green]{stats.n_success:,}[/]     "
            f"[grey46]Failed:[/] [red]{stats.n_failed:,}[/]     "
            f"[grey46]Skipped:[/] [yellow]{stats.n_skipped:,}[/]     "
            f"[grey46]Total:[/] {total}"
        )
    )


def time(elapsed_time: float):
    consol = console()

    markup = f"[grey46]Took:[/] {human_time(elapsed_time)}"
    consol.print(Text.from_markup(markup))


def job_header_line(job_id, width: int):
    consol = console()

    hdr = f"== [ Job {job_id} ] "
    width -= len(hdr)
    line = hdr + "=" * width
    consol.print(
        Text.from_markup(f"[grey42]{line}[/]")
    )
    consol.print(
        Text.from_markup("")
    )
