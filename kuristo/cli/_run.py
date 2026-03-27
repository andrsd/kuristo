from pathlib import Path

import yaml

import kuristo.config as config
import kuristo.utils as utils
from kuristo.exceptions import UserException
from kuristo.job import Job
from kuristo.plugin_loader import load_user_steps_from_kuristo_dir
from kuristo.resources import Resources
from kuristo.scanner import scan_locations
from kuristo.scheduler import Scheduler
from kuristo.workflow import parse_workflow_files


def _get_failed_job_nums(log_dir):
    """
    Read the latest run's report and return a set of failed job numbers (job.num).
    Raises UserException if no previous run exists or no jobs failed.
    Uses the 'id' field (job.num) which is stable when the same workflows are scanned in the same order.
    """
    report_path = log_dir / "runs" / "latest" / "report.yaml"
    if not report_path.exists():
        raise UserException("No previous run found. Cannot use --rerun-failed.")
    report = utils.read_report(report_path)
    failed = {r["id"] for r in report.get("results", []) if r.get("status") == "failed"}
    if not failed:
        raise UserException("No failed jobs found in the last run.")
    return failed


def create_results(jobs):
    """
    Built results from jobs. Jobs must be finished.

    @param jobs Jobs to produce results from. Pulled from `Scheduler`
    @return List of job results
    """
    results = []
    for job in jobs:
        if isinstance(job, Job):
            if job.is_skipped:
                results.append(
                    {
                        "id": job.num,
                        "job-name": job.name,
                        "status": "skipped",
                        "reason": job.skip_reason,
                    }
                )
            else:
                results.append(
                    {
                        "id": job.num,
                        "job-name": job.name,
                        "return-code": job.return_code,
                        "status": "success" if job.return_code == 0 else "failed",
                        "duration": round(job.elapsed_time, 3),
                    }
                )
    return results


def write_report_yaml(yaml_path: Path, results, total_runtime):
    with open(yaml_path, "w") as f:
        yaml.safe_dump({"results": results, "total-runtime": total_runtime}, f, sort_keys=False)


def run_jobs(args):
    locations = args.locations or ["."]

    cfg = config.get()
    out_dir = utils.create_run_output_dir(cfg.log_dir)

    # Get failed job numbers before updating the "latest" symlink
    failed_job_nums = None
    if args.rerun_failed or args.failed_first:
        failed_job_nums = _get_failed_job_nums(cfg.log_dir)

    utils.prune_old_runs(cfg.log_dir, cfg.log_history)
    utils.update_latest_symlink(cfg.log_dir, out_dir)

    load_user_steps_from_kuristo_dir()

    workflow_files = scan_locations(locations)
    workflows = parse_workflow_files(workflow_files)

    rcs = Resources()
    scheduler = Scheduler(
        workflows,
        rcs,
        out_dir,
        labels=args.labels,
        job_nums=failed_job_nums if args.rerun_failed else None,
        priority_job_nums=failed_job_nums if args.failed_first else None,
    )
    scheduler.check()
    scheduler.run_all_jobs()

    results = create_results(scheduler.jobs)
    yaml_path = out_dir / "report.yaml"
    write_report_yaml(yaml_path, results, scheduler.total_runtime)

    return scheduler.exit_code()
