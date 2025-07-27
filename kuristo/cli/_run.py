import yaml
from pathlib import Path
import kuristo.config as config
from kuristo.scheduler import Scheduler
from kuristo.resources import Resources
from kuristo.job import Job
from kuristo.plugin_loader import load_user_steps_from_kuristo_dir
from kuristo.job_spec import parse_workflow_files
from kuristo.scanner import scan_locations
from kuristo.utils import create_run_output_dir, prune_old_runs, update_latest_symlink


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


def write_report_yaml(yaml_path: Path, jobs, total_runtime):
    report = []
    for job in jobs:
        if isinstance(job, Job):
            if job.is_skipped:
                report.append({
                    "id": job.num,
                    "job name": job.name,
                    "status": "skipped",
                    "reason": job.skip_reason
                })
            else:
                report.append({
                    "id": job.num,
                    "job name": job.name,
                    "return code": job.return_code,
                    "status": "success" if job.return_code == 0 else "failed",
                    "duration": round(job.elapsed_time, 3)
                })

    with open(yaml_path, "w") as f:
        yaml.safe_dump({
            "results": report,
            "total_runtime": total_runtime
        }, f, sort_keys=False)


def update_report_yaml():
    pass


def run_jobs(args):
    locations = args.locations or ["."]

    cfg = config.get()
    if args.run_id:
        out_dir = create_run_output_dir(cfg.log_dir, args.run_id)
    else:
        out_dir = create_run_output_dir(cfg.log_dir)
        prune_old_runs(cfg.log_dir, cfg.log_history)
    update_latest_symlink(cfg.log_dir, out_dir)

    load_user_steps_from_kuristo_dir()

    workflow_files = scan_locations(locations)
    specs = parse_workflow_files(workflow_files)
    rcs = Resources()
    scheduler = Scheduler(specs, rcs, out_dir)
    scheduler.check()
    scheduler.run_all_jobs()

    if args.run_id:
        update_report_yaml()
    else:
        write_report_yaml(out_dir / "report.yaml", scheduler.jobs, scheduler.total_runtime)

    if args.report:
        write_report_csv(args.report_path, scheduler.jobs)

    return scheduler.exit_code()
