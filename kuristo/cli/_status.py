import kuristo.ui as ui
import kuristo.utils as utils
import kuristo.config as config
from rich.console import Console


STATUS_LABELS = {
    "success": "PASS",
    "failed": "FAIL",
    "skipped": "SKIP",
}


def summarize(results):
    counts = {"success": 0, "failed": 0, "skipped": 0}

    for r in results:
        status = r["status"]
        counts[status] += 1

    return ui.RunStats(counts['success'], counts['failed'], counts['skipped'])


def print_report(console: Console, report, no_ansi: bool):
    cfg = config.get()

    results = report.get("results", [])

    max_id_width = len(str(len(results)))

    max_label_len = cfg.console_width
    for r in results:
        max_label_len = max(max_label_len, len(r['job name']) + 1)

    for entry in results:
        ui.status_line(console, entry, STATUS_LABELS.get(entry["status"], "????"), max_id_width, max_label_len, no_ansi)
    stats = summarize(results)
    ui.line(console, cfg.console_width)
    ui.stats(console, stats)
    ui.time(console, report.get("total_runtime", 0.))


def status(args):
    try:
        console = Console(force_terminal=not args.no_ansi, no_color=args.no_ansi, markup=not args.no_ansi)

        cfg = config.get()
        run_name = args.run or "latest"
        runs_dir = cfg.log_dir / "runs" / run_name
        report_path = runs_dir / "report.yaml"
        if not report_path.exists():
            raise RuntimeError("No report found. Did you run any jobs yet?")

        report = utils.read_report(report_path)
        print_report(console, report, args.no_ansi)
    except Exception as e:
        print(e)
