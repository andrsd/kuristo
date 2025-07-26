from kuristo.config import Config
from kuristo.scheduler import Scheduler
from kuristo.resources import Resources
from kuristo.plugin_loader import load_user_steps_from_kuristo_dir
from kuristo.job_spec import parse_workflow_files
from kuristo.scanner import scan_locations
from kuristo.utils import create_run_output_dir, prune_old_runs, update_latest_symlink


def run_jobs(args):
    locations = args.location or ["."]

    config = Config()
    out_dir = create_run_output_dir(config.log_dir)
    prune_old_runs(config.log_dir, config.log_history)
    update_latest_symlink(config.log_dir, out_dir)

    load_user_steps_from_kuristo_dir()

    workflow_files = scan_locations(locations)
    specs = parse_workflow_files(workflow_files)
    rcs = Resources(config)
    scheduler = Scheduler(specs, rcs, out_dir, config=config, no_ansi=args.no_ansi, report_path=args.report)
    scheduler.check()
    scheduler.run_all_jobs()

    return scheduler.exit_code()
