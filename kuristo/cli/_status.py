import kuristo.ui as ui
import kuristo.utils as utils
import kuristo.config as config


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


def build_filters(args):
    filters = []
    if args.failed:
        filters.append("failed")
    if args.skipped:
        filters.append("skipped")
    if args.passed:
        filters.append("success")
    return filters


def print_report(report, filters: list):
    cfg = config.get()

    results = report.get("results", [])
    if not filters:
        filtered = results
    else:
        filtered = [r for r in results if r["status"] in filters]

    max_id_width = len(str(len(results)))

    max_label_len = cfg.console_width
    for r in filtered:
        max_label_len = max(max_label_len, len(r['job-name']) + 1)

    for entry in filtered:
        ui.status_line(entry, STATUS_LABELS.get(entry["status"], "????"), max_id_width, max_label_len)
    stats = summarize(filtered)
    ui.line(cfg.console_width)
    ui.stats(stats)
    ui.time(report.get("total-runtime", 0.))


def status(args):
    cfg = config.get()
    run_name = args.run_id or "latest"
    runs_dir = cfg.log_dir / "runs" / run_name
    report_path = runs_dir / "report.yaml"
    if not report_path.exists():
        raise RuntimeError("No report found. Did you run any jobs yet?")

    report = utils.read_report(report_path)
    filters = build_filters(args)
    print_report(report, filters)
