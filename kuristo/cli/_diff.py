from pathlib import Path

from packaging.version import parse as parse_version
from rich.table import Table
from rich.text import Text

import kuristo.config as config
import kuristo.ui as ui
import kuristo.utils as utils
from kuristo.exceptions import UserException

STATUS_LABELS = {
    "missing": "MISSING",
    "success": "PASS",
    "failed": "FAIL",
    "skipped": "SKIP",
}


def _load_report(run_identifier: str, log_dir: Path) -> dict:
    run_id = utils.resolve_run_id(log_dir, run_identifier)
    run_dir = utils.get_run_output_dir(log_dir, run_id)
    report_path = run_dir / "report.yaml"

    if not report_path.exists():
        raise UserException(f"Report file not found for run '{run_identifier}' at {report_path}")

    report_data = utils.read_report(report_path)

    report_version = report_data.get("version")
    if report_version is None:
        raise UserException(
            f"Report from run '{run_identifier}' does not specify a kuristo version. "
            "Cannot compare reports without version information."
        )

    min_comparable_version = parse_version("0.12.2.dev")
    current_report_version = parse_version(report_version)

    if current_report_version < min_comparable_version:
        raise UserException(
            f"Report from run '{run_identifier}' (version {report_version}) is too old. "
            f"Only reports with version {min_comparable_version} or newer can be compared "
            "because older reports lack 'workflow-file' information."
        )

    return report_data


def jobs_from_report(report):
    return {
        (job.get("workflow-file"), job.get("job-name")): job for job in report.get("results", [])
    }


def job_info(job):
    def status(job):
        status = job.get("status", "missing") if job else "missing"
        status = STATUS_LABELS[status]
        return status

    def duration(job):
        return utils.human_time(job.get("duration")) if job and "duration" in job else ""

    def return_code(job):
        return job.get("return-code") if job else None

    return (status(job), duration(job), return_code(job))


def diff(args):
    console = ui.console()

    cfg = config.get()
    log_dir = cfg.log_dir

    report1 = _load_report(args.run1, log_dir)
    report2 = _load_report(args.run2, log_dir)

    jobs1 = jobs_from_report(report1)
    jobs2 = jobs_from_report(report2)

    all_keys = sorted(list(set(jobs1.keys()) | set(jobs2.keys())))

    table = Table(
        show_lines=False,
        box=None,
    )
    table.add_column("Job name")
    table.add_column("Time", justify="right")

    for key in all_keys:
        wf_file, job_name = key
        job1 = jobs1.get(key)
        job2 = jobs2.get(key)

        status1, duration1, rc1 = job_info(job1)
        status2, duration2, rc2 = job_info(job2)

        if rc1 != rc2:
            table.add_row(
                Text(job_name, style="bold cyan"),
                Text(""),
            )

            if rc1 is not None:
                table.add_row(
                    Text(f"- {status1}: {rc1}", style="red"),
                    Text(duration1, style="red"),
                )
            if rc2 is not None:
                table.add_row(
                    Text(f"- {status2}: {rc2}", style="green"),
                    Text(duration2, style="green"),
                )

    if table.row_count > 0:
        console.print(table)
    else:
        console.print(Text("No difference"))

    return 0
