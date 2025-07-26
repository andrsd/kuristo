from dataclasses import dataclass
from rich.console import Console
from rich.text import Text
from kuristo.job import Job
from kuristo._utils import rich_job_name, human_time, human_time2


@dataclass
class RunStats:
    # Number of successful
    n_success: int
    # NUmber of failed
    n_failed: int
    # Number of skipped
    n_skipped: int


def padded_job_id(job_id, max_width):
    return f"{job_id:>{max_width}}"


def status_line(console: Console, job, state, max_id_width, max_label_len, no_ansi):
    if isinstance(job, Job):
        job_id = padded_job_id(job.id, max_id_width)
        job_name_len = len(job.name)
        job_name = rich_job_name(job.name)
        if job.is_skipped:
            skip_reason = job.skip_reason
        else:
            skip_reason = ""
        elapsed_time = job.elapsed_time
    elif isinstance(job, dict):
        job_id = padded_job_id(job["id"], max_id_width)
        job_name_len = len(job["job name"])
        job_name = rich_job_name(job["job name"])
        skip_reason = ""
        elapsed_time = job.get("duration", 0.0)
    else:
        raise ValueError("job parameter must be a dict of Job")
    time_str = human_time2(elapsed_time)
    width = max_label_len - 15 - job_name_len - len(time_str)
    dots = "." * width

    if state == "STARTING":
        if no_ansi:
            markup = f"         #{job_id} {job_name} "
            console.print(Text.from_markup(markup))
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
        console.print(Text.from_markup(markup))


def line(console: Console, width: int):
    line = "-" * width
    console.print(
        Text.from_markup(f"[grey23]{line}[/]")
    )


def stats(console: Console, stats: RunStats):
    total = stats.n_success + stats.n_failed + stats.n_skipped

    console.print(
        Text.from_markup(
            f"[grey46]Success:[/] [green]{stats.n_success:,}[/]     "
            f"[grey46]Failed:[/] [red]{stats.n_failed:,}[/]     "
            f"[grey46]Skipped:[/] [yellow]{stats.n_skipped:,}[/]     "
            f"[grey46]Total:[/] {total}"
        )
    )


def time(console: Console, elapsed_time: float):
    markup = f"[grey46]Took:[/] {human_time(elapsed_time)}"
    console.print(Text.from_markup(markup))
