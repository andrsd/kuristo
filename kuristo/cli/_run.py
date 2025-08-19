import yaml
from pathlib import Path
import kuristo.config as config
import kuristo.utils as utils
from kuristo.scheduler import Scheduler
from kuristo.resources import Resources
from kuristo.job import Job
from kuristo.plugin_loader import load_user_steps_from_kuristo_dir
from kuristo.job_spec import parse_workflow_files
from kuristo.scanner import scan_locations


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
                    "job-name": job.name,
                    "status": "skipped",
                    "reason": job.skip_reason
                })
            else:
                results.append({
                    "id": job.num,
                    "job-name": job.name,
                    "return-code": job.return_code,
                    "status": "success" if job.return_code == 0 else "failed",
                    "duration": round(job.elapsed_time, 3)
                })
    return results


def write_report_yaml(yaml_path: Path, results, total_runtime):
    with open(yaml_path, "w") as f:
        yaml.safe_dump({
            "results": results,
            "total-runtime": total_runtime
        }, f, sort_keys=False)


def run_jobs(args):
    locations = args.locations or ["."]

    cfg = config.get()
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
    write_report_yaml(yaml_path, results, scheduler.total_runtime)

    return scheduler.exit_code()
