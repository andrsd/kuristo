import yaml
import fcntl
import os
from pathlib import Path
import kuristo.config as config
import kuristo.utils as utils
from kuristo.scheduler import Scheduler
from kuristo.resources import Resources
from kuristo.job import Job
from kuristo.plugin_loader import load_user_steps_from_kuristo_dir
from kuristo.job_spec import parse_workflow_files
from kuristo.scanner import scan_locations


def write_report_csv(csv_path: Path, jobs):
    import csv
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "job name", "status", "duration [s]", "return code"])
        for job in jobs:
            duration = "" if job.is_skipped else round(job.elapsed_time, 3)
            if job.is_skipped:
                status = "skipped"
            elif job.return_code == 0:
                status = "success"
            else:
                status = "failed"
            writer.writerow([job.num, job.name, status, duration, job.return_code])


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
                results.append({
                    "id": job.num,
                    "job name": job.name,
                    "status": "skipped",
                    "reason": job.skip_reason
                })
            else:
                results.append({
                    "id": job.num,
                    "job name": job.name,
                    "return code": job.return_code,
                    "status": "success" if job.return_code == 0 else "failed",
                    "duration": round(job.elapsed_time, 3)
                })
    return results


def write_report_yaml(yaml_path: Path, results, total_runtime):
    with open(yaml_path, "w") as f:
        yaml.safe_dump({
            "results": results,
            "total_runtime": total_runtime
        }, f, sort_keys=False)


def update_report_atomic(yaml_path: Path, new_results: list):
    """
    Append new results into a yaml file

    @param yaml_path File we want to update
    @param new_results Results to add
    """
    yaml_path = Path(yaml_path)
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(yaml_path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)

        f.seek(0)
        try:
            report = yaml.safe_load(f) or {"results": []}
            results = report['results']
        except yaml.YAMLError:
            results = []

        results.extend(new_results)

        tmp_path = yaml_path.with_suffix(".tmp")
        write_report_yaml(tmp_path, results, 0.)

        os.replace(tmp_path, yaml_path)


def run_jobs(args):
    locations = args.locations or ["."]

    cfg = config.get()
    if args.run_id:
        out_dir = utils.create_run_output_dir(cfg.log_dir, args.run_id)
    else:
        out_dir = utils.create_run_output_dir(cfg.log_dir)
        utils.prune_old_runs(cfg.log_dir, cfg.log_history)
    utils.update_latest_symlink(cfg.log_dir, out_dir)

    load_user_steps_from_kuristo_dir()

    workflow_files = scan_locations(locations)
    specs = parse_workflow_files(workflow_files)
    rcs = Resources()
    scheduler = Scheduler(specs, rcs, out_dir)
    scheduler.check()
    scheduler.run_all_jobs()

    results = create_results(scheduler.jobs)
    yaml_path = out_dir / "report.yaml"
    if args.run_id:
        update_report_atomic(yaml_path, results)
    else:
        write_report_yaml(yaml_path, results, scheduler.total_runtime)

    if args.report:
        write_report_csv(args.report_path, scheduler.jobs)

    return scheduler.exit_code()
