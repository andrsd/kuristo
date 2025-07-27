import kuristo.config as config
from kuristo.scheduler import Scheduler
from kuristo.resources import Resources
from kuristo.plugin_loader import load_user_steps_from_kuristo_dir
from kuristo.job_spec import parse_workflow_files
from kuristo.scanner import scan_locations
from kuristo.utils import create_run_output_dir, prune_old_runs, update_latest_symlink


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
    scheduler = Scheduler(specs, rcs, out_dir, report_path=args.report)
    scheduler.check()
    scheduler.run_all_jobs()

    return scheduler.exit_code()
