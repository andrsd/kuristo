from rich.table import Table
import kuristo.utils as utils
import kuristo.config as config
import kuristo.ui as ui


def log(args):
    console = ui.console()

    cfg = config.get()
    runs_dir = cfg.log_dir / "runs"
    if not runs_dir.exists():
        raise RuntimeError("No runs found.")

    latest_tag = runs_dir / "latest"
    latest_target = None
    if latest_tag.is_symlink():
        try:
            latest_target = latest_tag.resolve().name
        except Exception:
            pass

    run_dirs = [
        d for d in runs_dir.iterdir()
        if d.is_dir() and d.name != "latest"
    ]
    run_dirs.sort(key=lambda d: d.name, reverse=False)

    table = Table(show_lines=False, box=None)

    table.add_column("Run ID", style="bold cyan", no_wrap=True)
    table.add_column("Duration", justify="right")
    table.add_column("Jobs", justify="right")
    table.add_column("Tag", style="green")

    for run_dir in run_dirs:
        report_file = run_dir / "report.yaml"
        if report_file.exists():
            try:
                report = utils.read_report(report_file)
                results = report.get("results", [])
                duration = report.get("total-runtime", 0)
                duration_str = f"{duration:.3f}s"
                job_count = str(len(results))
            except Exception:
                duration_str = "error"
                job_count = "?"
        else:
            duration_str = "error"
            job_count = "?"

        tag = "latest" if run_dir.name == latest_target else ""
        table.add_row(run_dir.name, duration_str, job_count, tag)

    console.print(table)
