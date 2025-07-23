from ..config import Config
from ..scheduler import Scheduler
from ..resources import Resources
from .._plugin_loader import load_user_steps_from_kuristo_dir
from ..job_spec import parse_workflow_files
from ..scanner import scan_locations
from .._utils import create_run_output_dir, prune_old_runs, update_latest_symlink


def run_jobs(args):
    locations = args.location or ["."]

    config = Config()
    log_dir = create_run_output_dir(config.log_dir)
    runs_dir = config.log_dir / "runs"
    prune_old_runs(runs_dir, config.log_history)
    update_latest_symlink(runs_dir, log_dir)

    load_user_steps_from_kuristo_dir()

    workflow_files = scan_locations(locations)
    specs = parse_workflow_files(workflow_files)
    rcs = Resources(config)
    scheduler = Scheduler(specs, rcs, log_dir, config=config, no_ansi=args.no_ansi, report_path=args.report)
    scheduler.check()
    scheduler.run_all_jobs()

    return scheduler.exit_code()
