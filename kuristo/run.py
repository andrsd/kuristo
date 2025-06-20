import re
import sys
import shutil
from datetime import datetime
from pathlib import Path
from .config import Config
from .scheduler import Scheduler
from .resources import Resources
from ._plugin_loader import load_user_steps_from_kuristo_dir
from ._utils import scan_locations, parse_tests_files
from .action_factory import register_actions


RUN_DIR_PATTERN = re.compile(r"\d{8}_\d{6}")


def create_run_output_dir(base_log_dir: Path) -> Path:
    runs_dir = base_log_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = runs_dir / timestamp
    run_dir.mkdir()
    return run_dir


def update_latest_symlink(runs_dir: Path, latest_run_dir: Path):
    """
    Create or update a symlink named 'latest' inside base_log_dir that points to latest_run_dir.
    """
    latest_link = runs_dir / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    relative_target = latest_run_dir.relative_to(runs_dir)
    latest_link.symlink_to(relative_target, target_is_directory=True)


def prune_old_runs(runs_dir: Path, keep_last_n: int):
    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and RUN_DIR_PATTERN.match(d.name)]
    run_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    for old_run in run_dirs[keep_last_n:]:
        shutil.rmtree(old_run)


def run_tests(args):
    locations = args.location or ["."]

    config = Config()
    log_dir = create_run_output_dir(config.log_dir)
    runs_dir = config.log_dir / "runs"
    prune_old_runs(runs_dir, config.log_history)
    update_latest_symlink(runs_dir, log_dir)

    register_actions()
    load_user_steps_from_kuristo_dir()

    tests_files = scan_locations(locations)
    tests = parse_tests_files(tests_files)
    rcs = Resources(config)
    scheduler = Scheduler(tests, rcs, log_dir)
    scheduler.check()
    scheduler.run_all_jobs()

    if scheduler.num_failed > 0:
        return 1
    else:
        return 0
