import kuristo._print as prn
import kuristo._utils as utils
from kuristo.config import Config
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

    return prn.RunStats(counts['success'], counts['failed'], counts['skipped'])


def print_report(console: Console, report, no_ansi: bool):
    results = report.get("results", [])

    max_id_width = len(str(len(results)))

    max_label_len = 80
    for r in results:
        max_label_len = max(max_label_len, len(r['job name']) + 1)

    for entry in results:
        prn.status_line(console, entry, STATUS_LABELS.get(entry["status"], "????"), max_id_width, max_label_len, no_ansi)
    stats = summarize(results)
    prn.line(console, max_label_len + 12 + max_id_width)
    prn.stats(console, stats)
    prn.time(console, report.get("total_runtime", 0.))


def status(args):
    try:
        console = Console(force_terminal=not args.no_ansi, no_color=args.no_ansi, markup=not args.no_ansi)

        config = Config()
        run_name = args.run or "latest"
        runs_dir = config.log_dir / "runs" / run_name
        report_path = runs_dir / "report.yaml"
        if not report_path.exists():
            raise RuntimeError("No report found. Did you run any jobs yet?")

        report = utils.read_report(report_path)
        print_report(console, report, args.no_ansi)
    except Exception as e:
        print(e)
